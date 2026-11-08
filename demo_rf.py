"""Roteiro de demonstração dos 10 requisitos funcionais.

Rode com:  python demo_rf.py

Usa o ProvedorFicticio e respostas simuladas da API para que o resultado
seja sempre o mesmo, independentemente do clima do dia ou da internet.
"""
import json
import time
from unittest import mock

import requests

import main  # também configura o terminal para UTF-8
from classes import (
    GeradorConsoleCreator, GeradorCSVCreator, GeradorJSONCreator, LeituraClima,
    ProvedorCache, ProvedorClima, ProvedorFicticio, ProvedorOpenMeteo,
)
from main import alertas, avaliar_alertas_ativos, coletar_resultados


def titulo(rf: str, texto: str) -> None:
    print(f"\n{'═' * 64}\n  {rf} · {texto}\n{'═' * 64}")


class FacadeSimulada:
    """Imita a OpenMeteoFacade devolvendo um JSON fixo (sem internet)."""
    def obter_clima_completo(self, cidade):
        return {"localidade": {"nome": cidade, "estado": "Alagoas", "pais": "Brasil"},
                "current": {"temperature_2m": 29.5, "relative_humidity_2m": 75,
                            "rain": 6.0, "wind_speed_10m": 33.0}}


class ProvedorContador(ProvedorClima):
    """Provedor que conta quantas vezes foi chamado (simula a rede)."""
    def __init__(self):
        self.chamadas = 0

    def obter_leitura(self, cidade):
        self.chamadas += 1
        time.sleep(0.5)  # simula a latência de uma requisição real
        return ProvedorFicticio().obter_leitura(cidade)


def rf1():
    titulo("RF1", "Dados climáticos protegidos")
    casos = {
        "temperatura ausente (None)": ("Maceió", None, 80, 0, 10),
        "umidade de 150%": ("Maceió", 30, 150, 0, 10),
        "chuva negativa": ("Maceió", 30, 80, -3, 10),
        "temperatura em texto": ("Maceió", "trinta", 80, 0, 10),
    }
    for descricao, args in casos.items():
        try:
            LeituraClima(*args)
            print(f"  ❌ {descricao}: aceita (erro!)")
        except ValueError as e:
            print(f"  ✅ {descricao}: rejeitada → {e}")
    print(f"  ✅ leitura válida criada: {LeituraClima('Maceió', 30, 80, 0, 10)}")


def rf2():
    titulo("RF2", "Calculado, não atribuível")
    leitura = LeituraClima("Maceió", 32.0, 90.0, 0.0, 10.0)
    for campo in ("temperatura", "umidade", "sensacao_termica"):
        try:
            setattr(leitura, campo, 0)
            print(f"  ❌ leitura.{campo} = 0 foi aceito (erro!)")
        except AttributeError:
            print(f"  ✅ leitura.{campo} = 0 → bloqueado (AttributeError)")
    print(f"  ✅ sensação térmica calculada na hora: {leitura.sensacao_termica}°C "
          f"(temperatura real {leitura.temperatura}°C)")


def rf3():
    titulo("RF3", "Múltiplas categorias de alerta")
    leitura = LeituraClima("Maceió", 34.0, 85.0, 32.0, 65.0)
    print(f"  Mesma leitura para todos: {leitura}")
    for alerta in alertas:
        print(f"  • {alerta.nome:<14} → {alerta.avaliar_risco(leitura)}")


def rf4():
    titulo("RF4", "Alertas autodescritivos")
    for alerta in alertas:
        print(f"  {alerta}")


def rf5():
    titulo("RF5", "Avaliação uniforme")
    leitura = LeituraClima("Rio Largo", 31.0, 72.0, 12.0, 45.0)
    print("  avaliar_alertas_ativos() percorre a lista mista sem saber os tipos:")
    for a in avaliar_alertas_ativos(leitura):
        print(f"  {a.nivel} · {a.categoria}")


def rf6():
    titulo("RF6", "Provedores de dados intercambiáveis")
    for nome, provedor in (("ProvedorFicticio", ProvedorFicticio()),
                           ("ProvedorOpenMeteo (Adapter)", ProvedorOpenMeteo(FacadeSimulada()))):
        r = coletar_resultados(provedor, ["Satuba"])[0]
        print(f"  {nome:<28} → {r.leitura} · maior risco: {r.maior_risco}")
    print("  ✅ a mesma função coletar_resultados() funcionou com os dois provedores")


def rf7():
    titulo("RF7", "Monitoramento de múltiplas localidades")
    resultados = coletar_resultados(ProvedorFicticio(), main.cidades)
    GeradorConsoleCreator().gerar_relatorio(resultados)


def rf8():
    titulo("RF8", "Falha graciosa")
    cenarios = {
        "API inacessível": requests.ConnectionError(),
        "tempo esgotado": requests.Timeout(),
        "JSON malformado": [mock.Mock(status_code=200, json=mock.Mock(side_effect=ValueError()))],
        "cidade inexistente": [mock.Mock(status_code=200, json=mock.Mock(return_value={"results": []}))],
    }
    for nome, efeito in cenarios.items():
        with mock.patch("api.requests.get", side_effect=efeito):
            r = coletar_resultados(ProvedorOpenMeteo(), ["Atlântida"])[0]
        print(f"  ✅ {nome:<18} → erro tratado: {r.erro}")
    print("  ✅ o programa continuou executando após todas as falhas")


def rf9():
    titulo("RF9", "Múltiplos formatos de relatório")
    resultados = coletar_resultados(ProvedorFicticio(), main.cidades[:2])
    GeradorCSVCreator("demo_relatorio.csv", com_resumo=False).gerar_relatorio(resultados)
    GeradorJSONCreator("demo_relatorio.json", com_resumo=False).gerar_relatorio(resultados)
    with open("demo_relatorio.json", encoding="utf-8") as f:
        primeiro = json.load(f)["resultados"][0]
    print("  Trecho do JSON gerado:")
    print("  " + json.dumps({k: primeiro[k] for k in ("cidade", "status", "leitura", "maior_risco")},
                            ensure_ascii=False))


def rf10():
    titulo("RF10", "Cache transparente")
    real = ProvedorContador()
    provedor = ProvedorCache(real, ttl_segundos=300)
    for i in range(1, 4):
        inicio = time.perf_counter()
        provedor.obter_leitura("Maceió")
        ms = (time.perf_counter() - inicio) * 1000
        print(f"  consulta {i}: {ms:6.1f} ms · chamadas ao provedor real até agora: {real.chamadas}")
    print("  ✅ 3 consultas, apenas 1 chamada real: as demais vieram do cache")


if __name__ == "__main__":
    for demo in (rf1, rf2, rf3, rf4, rf5, rf6, rf7, rf8, rf9, rf10):
        demo()
    print()
