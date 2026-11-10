"""Testes automatizados do sistema. Rode com:  python -m unittest testes -v

Não dependem de internet: as respostas da API são simuladas.
"""
import contextlib
import csv
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import requests

import main
from api import OpenMeteoFacade
from classes import (
    AlertaAlagamento, AlertaCalor, AlertaGeada, AlertaTempestade, AlertaVento, ExportadorComResumo,
    ExportadorConsole, GeradorCSVCreator, GeradorJSONCreator, LeituraClima, NivelRisco, ProvedorCache,
    ProvedorClima, ProvedorFicticio, ProvedorOpenMeteo, ResultadoCidade,
)


def resposta_falsa(corpo=None, status=200, texto=None):
    resp = mock.Mock(status_code=status)
    if texto is not None:
        resp.json.side_effect = requests.JSONDecodeError("inválido", texto, 0)
    else:
        resp.json.return_value = corpo
    resp.raise_for_status.side_effect = requests.HTTPError(f"{status}") if status >= 400 else None
    return resp


GEO_OK = {"results": [{"name": "Maceió", "admin1": "Alagoas", "country": "Brasil",
                       "latitude": -9.66, "longitude": -35.73}]}
CLIMA_OK = {"current": {"temperature_2m": 33.0, "relative_humidity_2m": 82,
                        "rain": 16.0, "wind_speed_10m": 45.0}}


class FacadeFalsa:
    def __init__(self, retorno):
        self.retorno = retorno

    def obter_clima_completo(self, cidade):
        return self.retorno


def silencioso(func, *args):
    with contextlib.redirect_stdout(io.StringIO()) as saida:
        func(*args)
    return saida.getvalue()


class TestRF1DadosProtegidos(unittest.TestCase):
    def test_valores_invalidos_sao_rejeitados(self):
        casos = [(None, 50, 0, 0), (25, 150, 0, 0), (25, 50, -1, 0), (25, 50, 0, -5),
                 ("25", 50, 0, 0), (float("nan"), 50, 0, 0), (True, 50, 0, 0), (200, 50, 0, 0)]
        for t, u, c, v in casos:
            with self.subTest(t=t, u=u, c=c, v=v), self.assertRaises(ValueError):
                LeituraClima("X", t, u, c, v)

    def test_leitura_valida(self):
        lt = LeituraClima("Maceió", 27, 78, 0, 22.6)
        self.assertEqual(lt.temperatura, 27.0)
        self.assertIsInstance(lt.umidade, float)


class TestRF2NaoAtribuivel(unittest.TestCase):
    def test_atributos_somente_leitura(self):
        lt = LeituraClima("Maceió", 27, 78, 0, 10)
        for campo in ("cidade", "temperatura", "umidade", "chuva", "vento", "sensacao_termica"):
            with self.subTest(campo=campo), self.assertRaises(AttributeError):
                setattr(lt, campo, 1)

    def test_sensacao_termica_calculada(self):
        self.assertGreater(LeituraClima("X", 32, 90, 0, 0).sensacao_termica, 32)


class TestRF3RF4RF5Alertas(unittest.TestCase):
    def test_cada_categoria_tem_criterio_proprio(self):
        calor = LeituraClima("X", 39, 50, 0, 0)
        chuva = LeituraClima("X", 25, 90, 35, 0)
        frio = LeituraClima("X", -1, 50, 0, 0)
        vento = LeituraClima("X", 25, 50, 0, 95)
        self.assertEqual(AlertaCalor().avaliar_risco(calor), NivelRisco.ALTO)
        self.assertEqual(AlertaAlagamento().avaliar_risco(chuva), NivelRisco.CRITICO)
        self.assertEqual(AlertaTempestade().avaliar_risco(chuva), NivelRisco.ALTO)
        self.assertEqual(AlertaGeada().avaliar_risco(frio), NivelRisco.ALTO)
        self.assertEqual(AlertaVento().avaliar_risco(vento), NivelRisco.CRITICO)
        self.assertEqual(AlertaVento().avaliar_risco(calor), NivelRisco.NENHUM)

    def test_autodescricao(self):
        textos = [str(a) for a in main.alertas]
        self.assertEqual(len(set(textos)), len(main.alertas))
        self.assertIn("Calor", textos[0])

    def test_avaliacao_uniforme(self):
        ativos = main.avaliar_alertas_ativos(LeituraClima("X", 34, 85, 32, 25))
        self.assertEqual({a.categoria for a in ativos}, {"Calor extremo", "Alagamento", "Tempestade"})


class TestRF6RF7Provedores(unittest.TestCase):
    def test_provedores_intercambiaveis(self):
        adaptado = ProvedorOpenMeteo(FacadeFalsa({"localidade": {"nome": "Maceió"}, **CLIMA_OK}))
        for provedor in (ProvedorFicticio(), adaptado):
            with self.subTest(provedor=type(provedor).__name__):
                resultados = main.coletar_resultados(provedor, ["Maceió"])
                self.assertFalse(resultados[0].erro)

    def test_varias_cidades_um_relatorio(self):
        resultados = main.coletar_resultados(ProvedorFicticio(), ["Maceió", "Satuba", "Rio Largo"])
        self.assertEqual([r.cidade for r in resultados], ["Maceió", "Satuba", "Rio Largo"])


class TestRF8FalhaGraciosa(unittest.TestCase):
    def _coletar_com_get(self, efeito):
        with mock.patch("api.requests.get", side_effect=efeito):
            return main.coletar_resultados(ProvedorOpenMeteo(), ["Maceió"])[0]

    def test_api_inacessivel(self):
        self.assertIn("inacessível", self._coletar_com_get(requests.ConnectionError()).erro)

    def test_timeout(self):
        self.assertIn("esgotado", self._coletar_com_get(requests.Timeout()).erro)

    def test_localidade_inexistente(self):
        r = self._coletar_com_get([resposta_falsa({"generationtime_ms": 0.1})])
        self.assertIn("desconhecida", r.erro)

    def test_json_malformado(self):
        casos = {
            "corpo não JSON": [resposta_falsa(texto="<html>")],
            "lista em vez de objeto": [resposta_falsa([1, 2])],
            "results não é lista": [resposta_falsa({"results": "x"})],
            "sem coordenadas": [resposta_falsa({"results": [{"name": "X"}]})],
            "sem current": [resposta_falsa(GEO_OK), resposta_falsa({"hourly": {}})],
            "campo ausente": [resposta_falsa(GEO_OK), resposta_falsa({"current": {"temperature_2m": 20}})],
            "campo texto": [resposta_falsa(GEO_OK), resposta_falsa(
                {"current": {**CLIMA_OK["current"], "rain": "muita"}})],
        }
        for nome, respostas in casos.items():
            with self.subTest(caso=nome):
                self.assertTrue(self._coletar_com_get(respostas).erro)

    def test_erro_http_com_motivo(self):
        r = self._coletar_com_get([resposta_falsa({"error": True, "reason": "Latitude inválida"}, status=400)])
        self.assertIn("Latitude inválida", r.erro)

    def test_resposta_valida_completa(self):
        r = self._coletar_com_get([resposta_falsa(GEO_OK), resposta_falsa(CLIMA_OK)])
        self.assertEqual(r.leitura.regiao, "Alagoas, Brasil")
        self.assertEqual(r.maior_risco, NivelRisco.ALTO)


class TestRF9Relatorios(unittest.TestCase):
    def setUp(self):
        self.resultados = [
            ResultadoCidade.Builder("Maceió").com_leitura(LeituraClima("Maceió", 34, 85, 32, 25, "AL"))
            .com_alertas(main.avaliar_alertas_ativos(LeituraClima("Maceió", 34, 85, 32, 25))).build(),
            ResultadoCidade.Builder("Atlantida").com_erro("Localidade desconhecida").build(),
        ]
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)

    def test_json_estrutura_consistente(self):
        caminho = os.path.join(self.pasta.name, "r.json")
        silencioso(GeradorJSONCreator(caminho).gerar_relatorio, self.resultados)
        with open(caminho, encoding="utf-8") as f:
            doc = json.load(f)
        self.assertEqual(doc["total_cidades"], 2)
        ok, erro = doc["resultados"]
        self.assertEqual(set(ok), set(erro))  # mesmas chaves nos dois casos
        self.assertEqual(ok["status"], "ok")
        self.assertEqual(ok["maior_risco"], "CRÍTICO")
        self.assertEqual(ok["alertas"][0]["nivel"], "CRÍTICO")  # ordenado por gravidade
        self.assertEqual(erro["status"], "erro")
        self.assertIsNone(erro["leitura"])

    def test_csv(self):
        caminho = os.path.join(self.pasta.name, "r.csv")
        silencioso(GeradorCSVCreator(caminho).gerar_relatorio, self.resultados)
        with open(caminho, encoding="utf-8-sig", newline="") as f:
            linhas = list(csv.reader(f, delimiter=";"))
        self.assertEqual(len(linhas), 3)
        self.assertEqual(linhas[2][-1], "Localidade desconhecida")

    def test_decorator_adiciona_resumo(self):
        saida = silencioso(ExportadorComResumo(ExportadorConsole()).exportar, self.resultados)
        self.assertIn("RELATÓRIO CLIMÁTICO", saida)
        self.assertIn("📊 Resumo: 2 cidade(s)", saida)


class TestRF10Cache(unittest.TestCase):
    def test_cache_transparente(self):
        real = mock.Mock(spec=ProvedorClima)
        real.obter_leitura.return_value = LeituraClima("Maceió", 27, 78, 0, 10)
        cache = ProvedorCache(real, ttl_segundos=60)
        a = cache.obter_leitura("Maceió")
        b = cache.obter_leitura(" maceió ")
        self.assertIs(a, b)
        self.assertEqual(real.obter_leitura.call_count, 1)

    def test_cache_expira(self):
        real = mock.Mock(spec=ProvedorClima)
        real.obter_leitura.return_value = LeituraClima("Maceió", 27, 78, 0, 10)
        cache = ProvedorCache(real, ttl_segundos=0)
        cache.obter_leitura("Maceió")
        cache.obter_leitura("Maceió")
        self.assertEqual(real.obter_leitura.call_count, 2)


class TestMenu(unittest.TestCase):
    def test_menu_nao_trava_com_entradas_ruins(self):
        entradas = iter(["abc", "1", "Inexistente", "5", "", "6", "7"])
        with mock.patch("builtins.input", lambda _: next(entradas)):
            saida = silencioso(main.main)
        self.assertIn("Opção inválida", saida)
        self.assertIn("não está na lista", saida)
        self.assertIn("Até logo", saida)

    def test_menu_encerra_com_ctrl_d(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            self.assertIn("Até logo", silencioso(main.main))


if __name__ == "__main__":
    unittest.main(verbosity=2)
