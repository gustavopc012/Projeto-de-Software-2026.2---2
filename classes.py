import csv
import json
import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from api import OpenMeteoFacade


# ==========================================================================
# NÍVEIS DE RISCO
# ==========================================================================
class NivelRisco(Enum):
    NENHUM = "NENHUM"
    BAIXO = "BAIXO"
    MEDIO = "MÉDIO"
    ALTO = "ALTO"
    CRITICO = "CRÍTICO"

    @property
    def peso(self) -> int:
        """Ordem de gravidade, usada para comparar e ordenar riscos."""
        return list(NivelRisco).index(self)

    @property
    def emoji(self) -> str:
        return {"NENHUM": "⚪", "BAIXO": "🟢", "MÉDIO": "🟡", "ALTO": "🟠", "CRÍTICO": "🔴"}[self.value]

    def __str__(self) -> str:
        return f"{self.emoji} {self.value}"


# ==========================================================================
# LEITURA CLIMÁTICA (objeto de domínio)
# ==========================================================================
class LeituraClima:
    """Leitura climática imutável e sempre válida."""

    # Faixas físicas aceitas. Fora delas, a leitura é rejeitada.
    LIMITES = {
        "temperatura": (-90.0, 60.0),   # °C
        "umidade": (0.0, 100.0),        # %
        "chuva": (0.0, 500.0),          # mm
        "vento": (0.0, 400.0),          # km/h
    }

    def __init__(self, cidade: str, temperatura: float, umidade: float,
                 chuva: float, vento: float = 0.0, regiao: str = ""):
        # [RF1] Dados climáticos protegidos: tudo é validado ANTES de o objeto
        # existir. Se algo estiver ausente, não numérico ou fora da faixa
        # física, o construtor lança ValueError e nenhuma leitura inválida
        # chega a ser criada.
        if not isinstance(cidade, str) or not cidade.strip():
            raise ValueError("Nome da cidade ausente na leitura")

        self._cidade = cidade.strip()
        self._regiao = (regiao or "").strip()
        self._temperatura = self._validar("temperatura", temperatura)
        self._umidade = self._validar("umidade", umidade)
        self._chuva = self._validar("chuva", chuva)
        self._vento = self._validar("vento", vento)

    @classmethod
    def _validar(cls, campo: str, valor) -> float:
        if valor is None:
            raise ValueError(f"Dado ausente na resposta da API: {campo}")
        # bool é subclasse de int em Python, mas não é um dado climático válido
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError(f"Valor não numérico para {campo}: {valor!r}")
        valor = float(valor)
        if not math.isfinite(valor):
            raise ValueError(f"Valor não finito para {campo}: {valor}")
        minimo, maximo = cls.LIMITES[campo]
        if not (minimo <= valor <= maximo):
            raise ValueError(f"{campo.capitalize()} fora da faixa [{minimo:g}, {maximo:g}]: {valor:g}")
        return valor

    # [RF2] Calculado, não atribuível: os atributos são expostos apenas por
    # @property sem setter. Tentar "leitura.temperatura = 40" gera
    # AttributeError, então nenhum código externo altera a leitura.
    @property
    def cidade(self) -> str:
        return self._cidade

    @property
    def regiao(self) -> str:
        return self._regiao

    @property
    def temperatura(self) -> float:
        return self._temperatura

    @property
    def umidade(self) -> float:
        return self._umidade

    @property
    def chuva(self) -> float:
        return self._chuva

    @property
    def vento(self) -> float:
        return self._vento

    @property
    def sensacao_termica(self) -> float:
        # [RF2] Valor DERIVADO: não é armazenado nem pode ser atribuído. É
        # recalculado a partir dos dados protegidos sempre que é lido.
        # Fórmula de temperatura aparente (Steadman / Australian BoM).
        pressao_vapor = (self._umidade / 100) * 6.105 * math.exp(
            17.27 * self._temperatura / (237.7 + self._temperatura))
        vento_ms = self._vento / 3.6
        return round(self._temperatura + 0.33 * pressao_vapor - 0.70 * vento_ms - 4.0, 1)

    def para_dict(self) -> dict:
        """Representação serializável (usada na exportação JSON)."""
        return {
            "temperatura_c": self._temperatura,
            "sensacao_termica_c": self.sensacao_termica,
            "umidade_pct": self._umidade,
            "chuva_mm": self._chuva,
            "vento_kmh": self._vento,
        }

    def __repr__(self) -> str:
        return (f"<{self._cidade}: {self._temperatura}°C, {self._umidade}%, "
                f"{self._chuva}mm, {self._vento}km/h>")


# ==========================================================================
# [RF3] Múltiplas categorias de alerta: Alerta é a abstração (classe
# abstrata) e cada subclasse aplica critérios próprios sobre a MESMA
# LeituraClima (herança). Há cinco categorias: Calor, Alagamento, Geada,
# Tempestade e Vento.
# ==========================================================================
@dataclass(frozen=True)
class AlertaAtivo:
    """Resultado imutável da avaliação de um alerta que disparou."""
    categoria: str
    icone: str
    nivel: NivelRisco
    mensagem: str


class Alerta(ABC):
    icone: str = "⚠️"

    @property
    @abstractmethod
    def nome(self) -> str: ...

    @property
    @abstractmethod
    def criterio(self) -> str: ...

    @abstractmethod
    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco: ...

    @abstractmethod
    def mensagem_alerta(self, leitura: LeituraClima) -> str: ...

    # [RF4] Alertas autodescritivos: cada categoria se descreve sozinha
    # (ícone, nome e critério). Basta fazer print(alerta) em uma lista
    # genérica, sem saber qual subclasse está sendo exibida.
    def __str__(self) -> str:
        return f"{self.icone} {self.nome}: {self.criterio}"


class AlertaCalor(Alerta):
    icone = "🔥"
    nome = "Calor extremo"
    criterio = "temperatura alta, agravada pela umidade"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.temperatura >= 38 or (leitura.temperatura >= 32 and leitura.umidade >= 80):
            return NivelRisco.ALTO
        if leitura.temperatura >= 32 or (leitura.temperatura >= 30 and leitura.umidade >= 70):
            return NivelRisco.MEDIO
        if leitura.temperatura >= 28:
            return NivelRisco.BAIXO
        return NivelRisco.NENHUM

    def mensagem_alerta(self, leitura: LeituraClima) -> str:
        return (f"Calor de {leitura.temperatura}°C (sensação de {leitura.sensacao_termica}°C) "
                f"com umidade de {leitura.umidade}%. Mantenha-se hidratado!")


class AlertaAlagamento(Alerta):
    icone = "🌊"
    nome = "Alagamento"
    criterio = "volume de chuva acumulado"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.chuva >= 30:
            return NivelRisco.CRITICO
        if leitura.chuva >= 15:
            return NivelRisco.ALTO
        if leitura.chuva >= 5:
            return NivelRisco.MEDIO
        if leitura.chuva > 0:
            return NivelRisco.BAIXO
        return NivelRisco.NENHUM

    def mensagem_alerta(self, leitura: LeituraClima) -> str:
        return f"Chuva de {leitura.chuva} mm em {leitura.cidade}. Evite vias com risco de alagamento!"


class AlertaGeada(Alerta):
    icone = "❄️"
    nome = "Geada"
    criterio = "temperatura próxima ou abaixo de 0°C"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.temperatura <= 0:
            return NivelRisco.ALTO
        if leitura.temperatura <= 4:
            return NivelRisco.MEDIO
        return NivelRisco.NENHUM

    def mensagem_alerta(self, leitura: LeituraClima) -> str:
        return f"Temperatura de {leitura.temperatura}°C em {leitura.cidade}. Proteja plantações e animais!"


class AlertaTempestade(Alerta):
    icone = "⛈️"
    nome = "Tempestade"
    criterio = "chuva forte combinada com umidade elevada"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.chuva >= 20 and leitura.umidade >= 85:
            return NivelRisco.ALTO
        if leitura.chuva >= 10:
            return NivelRisco.MEDIO
        return NivelRisco.NENHUM

    def mensagem_alerta(self, leitura: LeituraClima) -> str:
        return (f"Chuva de {leitura.chuva} mm com umidade de {leitura.umidade}%. "
                f"Atenção a raios e quedas de energia!")


class AlertaVento(Alerta):
    icone = "💨"
    nome = "Vento forte"
    criterio = "velocidade do vento a 10 m de altura"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.vento >= 90:
            return NivelRisco.CRITICO
        if leitura.vento >= 60:
            return NivelRisco.ALTO
        if leitura.vento >= 40:
            return NivelRisco.MEDIO
        if leitura.vento >= 30:
            return NivelRisco.BAIXO
        return NivelRisco.NENHUM

    def mensagem_alerta(self, leitura: LeituraClima) -> str:
        return f"Ventos de {leitura.vento} km/h. Cuidado com árvores e objetos soltos!"


# ==========================================================================
# PROVEDORES DE DADOS
# [RF6] Provedores intercambiáveis: a lógica de alertas depende apenas da
# abstração ProvedorClima. Qualquer implementação (OpenMeteo, Fictício, com
# ou sem cache) pode ser trocada no main.py sem alterar a avaliação.
# ==========================================================================
class ProvedorClima(ABC):  # Target (interface que o sistema conhece)
    @abstractmethod
    def obter_leitura(self, cidade: str) -> LeituraClima: ...


# --------------------------------------------------------------------------
# PADRÃO ESTRUTURAL: ADAPTER
# Converte o dicionário JSON devolvido pela Facade (o Adaptee) para a
# interface ProvedorClima, entregando objetos LeituraClima.
# --------------------------------------------------------------------------
class ProvedorOpenMeteo(ProvedorClima):
    def __init__(self, facade: OpenMeteoFacade | None = None):
        self._facade = facade or OpenMeteoFacade()  # Adaptee

    def obter_leitura(self, cidade: str) -> LeituraClima:
        dados = self._facade.obter_clima_completo(cidade)

        # [RF8] JSON malformado vira ValueError, que é tratado sem travar.
        if not isinstance(dados, dict):
            raise ValueError("Resposta da API em formato inesperado")
        atual = dados.get("current")
        local = dados.get("localidade") or {}
        if not isinstance(atual, dict) or not isinstance(local, dict):
            raise ValueError("Resposta da API em formato inesperado")

        regiao = ", ".join(p for p in (local.get("estado"), local.get("pais")) if p)

        # Tradução JSON -> domínio. A validação do RF1 ocorre no construtor.
        return LeituraClima(
            cidade=local.get("nome") or cidade,
            regiao=regiao,
            temperatura=atual.get("temperature_2m"),
            umidade=atual.get("relative_humidity_2m"),
            chuva=atual.get("rain"),
            vento=atual.get("wind_speed_10m"),
        )


class ProvedorFicticio(ProvedorClima):
    """Provedor offline com dados fixos, útil para demonstração e testes."""
    _DADOS = {
        "maceió": (34.0, 85.0, 32.0, 25.0),
        "rio largo": (31.0, 72.0, 12.0, 45.0),
        "marechal deodoro": (26.0, 60.0, 0.0, 12.0),
        "satuba": (29.0, 90.0, 22.0, 65.0),
    }

    def obter_leitura(self, cidade: str) -> LeituraClima:
        temp, umid, chuva, vento = self._DADOS.get(cidade.strip().casefold(), (24.0, 55.0, 0.0, 10.0))
        return LeituraClima(cidade.strip(), temp, umid, chuva, vento, regiao="dados fictícios")


# --------------------------------------------------------------------------
# PADRÃO ESTRUTURAL: PROXY (Caching Proxy)
# [RF10] Cache transparente: o proxy tem a mesma interface do provedor real.
# Consultas repetidas à mesma cidade dentro do TTL são servidas da memória,
# sem nova chamada de rede, e o código cliente não percebe a diferença.
# --------------------------------------------------------------------------
class ProvedorCache(ProvedorClima):
    def __init__(self, provedor_real: ProvedorClima, ttl_segundos: int = 300):
        self._provedor_real = provedor_real
        self._ttl = ttl_segundos
        self._cache: dict[str, tuple[LeituraClima, float]] = {}

    def obter_leitura(self, cidade: str) -> LeituraClima:
        chave = cidade.strip().casefold()  # "Maceió" e " maceió " são a mesma chave
        agora = time.monotonic()
        if chave in self._cache:
            leitura, instante = self._cache[chave]
            if agora - instante < self._ttl:
                return leitura  # cache hit: nenhuma requisição de rede
        leitura = self._provedor_real.obter_leitura(cidade)
        self._cache[chave] = (leitura, agora)
        return leitura


# ==========================================================================
# PADRÃO CRIACIONAL: BUILDER (ResultadoCidade)
# ==========================================================================
class ResultadoCidade:
    def __init__(self, builder: "ResultadoCidade.Builder"):
        self._cidade = builder.cidade
        self._leitura = builder.leitura
        self._alertas_ativos = tuple(sorted(builder.alertas_ativos, key=lambda a: a.nivel.peso, reverse=True))
        self._erro = builder.erro

    @property
    def cidade(self) -> str:
        return self._cidade

    @property
    def leitura(self) -> LeituraClima | None:
        return self._leitura

    @property
    def alertas_ativos(self) -> tuple[AlertaAtivo, ...]:
        return self._alertas_ativos

    @property
    def erro(self) -> str:
        return self._erro

    @property
    def maior_risco(self) -> NivelRisco:
        # [RF2] Valor derivado: calculado a partir dos alertas, não atribuído.
        return max((a.nivel for a in self._alertas_ativos), key=lambda n: n.peso, default=NivelRisco.NENHUM)

    def para_dict(self) -> dict:
        """Estrutura JSON consistente para sucesso e erro: sempre as mesmas chaves."""
        return {
            "cidade": self._cidade,
            "status": "erro" if self._erro else "ok",
            "localidade": None if self._leitura is None else {
                "nome": self._leitura.cidade, "regiao": self._leitura.regiao},
            "leitura": None if self._leitura is None else self._leitura.para_dict(),
            "maior_risco": None if self._erro else self.maior_risco.value,
            "alertas": [
                {"categoria": a.categoria, "nivel": a.nivel.value, "mensagem": a.mensagem}
                for a in self._alertas_ativos
            ],
            "erro": self._erro or None,
        }

    class Builder:
        def __init__(self, cidade: str):
            if not cidade or not cidade.strip():
                raise ValueError("O nome da cidade é obrigatório.")
            self.cidade = cidade.strip()
            self.leitura: LeituraClima | None = None
            self.alertas_ativos: list[AlertaAtivo] = []
            self.erro = ""

        def com_leitura(self, leitura: LeituraClima) -> "ResultadoCidade.Builder":
            self.leitura = leitura
            return self

        def com_alertas(self, alertas: list[AlertaAtivo]) -> "ResultadoCidade.Builder":
            self.alertas_ativos = list(alertas)
            return self

        def com_erro(self, mensagem_erro: str) -> "ResultadoCidade.Builder":
            self.erro = mensagem_erro
            return self

        def build(self) -> "ResultadoCidade":
            if self.leitura is None and not self.erro:
                raise ValueError(f"Resultado inválido para '{self.cidade}': informe uma leitura ou um erro.")
            if self.leitura is not None and self.erro:
                raise ValueError(f"Resultado inconsistente para '{self.cidade}': leitura e erro ao mesmo tempo.")
            return ResultadoCidade(self)


# ==========================================================================
# [RF9] Múltiplos formatos de relatório: Console, CSV e JSON. A escolha do
# formato fica desacoplada da geração dos dados via Factory Method.
# PADRÃO CRIACIONAL: FACTORY METHOD
# ==========================================================================
LINHA_DUPLA = "═" * 60
LINHA_SIMPLES = "─" * 60


class ExportadorRelatorio(ABC):  # Product
    @abstractmethod
    def exportar(self, resultados: list[ResultadoCidade]) -> None: ...


class ExportadorConsole(ExportadorRelatorio):
    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        print(f"\n{LINHA_DUPLA}")
        print(f"  🌦️  RELATÓRIO CLIMÁTICO · {datetime.now():%d/%m/%Y %H:%M}")
        print(LINHA_DUPLA)
        for res in resultados:
            if res.erro:
                print(f"\n📍 {res.cidade}")
                print(f"   ❌ Não foi possível obter os dados: {res.erro}")
            else:
                lt = res.leitura
                regiao = f" · {lt.regiao}" if lt.regiao else ""
                print(f"\n📍 {lt.cidade}{regiao}")
                print(f"   🌡️ {lt.temperatura:.1f}°C (sensação {lt.sensacao_termica:.1f}°C)  "
                      f"💧 {lt.umidade:.0f}%  🌧️ {lt.chuva:.1f} mm  💨 {lt.vento:.1f} km/h")
                if res.alertas_ativos:
                    for a in res.alertas_ativos:
                        print(f"   {a.nivel.emoji} {a.nivel.value:<8} {a.icone} {a.categoria}: {a.mensagem}")
                else:
                    print("   ✅ Sem alertas ativos")
            print(LINHA_SIMPLES)


class ExportadorCSV(ExportadorRelatorio):
    def __init__(self, destino: str = "relatorio.csv"):
        self._destino = destino

    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        with open(self._destino, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["Cidade", "Localidade", "Temperatura (°C)", "Sensação (°C)", "Umidade (%)",
                               "Chuva (mm)", "Vento (km/h)", "Maior risco", "Alertas ativos", "Erro"])
            for res in resultados:
                if res.erro:
                    escritor.writerow([res.cidade, "", "", "", "", "", "", "", "", res.erro])
                    continue
                lt = res.leitura
                alertas = " | ".join(f"{a.categoria} [{a.nivel.value}]" for a in res.alertas_ativos) or "Sem alertas"
                escritor.writerow([res.cidade, f"{lt.cidade} ({lt.regiao})" if lt.regiao else lt.cidade,
                                   lt.temperatura, lt.sensacao_termica, lt.umidade, lt.chuva, lt.vento,
                                   res.maior_risco.value, alertas, ""])
        print(f"\n💾 Relatório CSV salvo em '{self._destino}'")


class ExportadorJSON(ExportadorRelatorio):
    def __init__(self, destino: str = "relatorio.json"):
        self._destino = destino

    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        documento = {
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
            "total_cidades": len(resultados),
            "resultados": [res.para_dict() for res in resultados],
        }
        with open(self._destino, "w", encoding="utf-8") as arquivo:
            json.dump(documento, arquivo, ensure_ascii=False, indent=4)
        print(f"\n💾 Relatório JSON salvo em '{self._destino}'")


# --------------------------------------------------------------------------
# PADRÃO ESTRUTURAL: DECORATOR
# ExportadorComResumo envolve QUALQUER exportador (Console, CSV ou JSON),
# repassa a exportação para ele e acrescenta um resumo no terminal. Assim a
# funcionalidade extra é adicionada por composição, sem alterar nem criar
# subclasses de cada exportador concreto.
# --------------------------------------------------------------------------
class ExportadorComResumo(ExportadorRelatorio):
    def __init__(self, exportador: ExportadorRelatorio):
        self._exportador = exportador  # componente decorado

    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        self._exportador.exportar(resultados)  # comportamento original
        self._imprimir_resumo(resultados)      # comportamento acrescentado

    @staticmethod
    def _imprimir_resumo(resultados: list[ResultadoCidade]) -> None:
        ok = [r for r in resultados if not r.erro]
        com_alerta = [r for r in ok if r.alertas_ativos]
        erros = len(resultados) - len(ok)
        maior = max((r.maior_risco for r in ok), key=lambda n: n.peso, default=NivelRisco.NENHUM)
        print(f"📊 Resumo: {len(resultados)} cidade(s) · {len(com_alerta)} com alerta · "
              f"{erros} com erro · maior risco: {maior}")


class GeradorRelatorioCreator(ABC):  # Creator
    def __init__(self, com_resumo: bool = True):
        self._com_resumo = com_resumo

    @abstractmethod
    def criar_exportador(self) -> ExportadorRelatorio:
        """Factory Method: as subclasses decidem qual exportador concreto criar."""

    def gerar_relatorio(self, resultados: list[ResultadoCidade]) -> None:
        exportador = self.criar_exportador()
        if self._com_resumo:
            exportador = ExportadorComResumo(exportador)  # Decorator aplicado
        exportador.exportar(resultados)


class GeradorConsoleCreator(GeradorRelatorioCreator):
    def criar_exportador(self) -> ExportadorRelatorio:
        return ExportadorConsole()


class GeradorCSVCreator(GeradorRelatorioCreator):
    def __init__(self, destino: str = "relatorio.csv", com_resumo: bool = True):
        super().__init__(com_resumo)
        self._destino = destino

    def criar_exportador(self) -> ExportadorRelatorio:
        return ExportadorCSV(self._destino)


class GeradorJSONCreator(GeradorRelatorioCreator):
    def __init__(self, destino: str = "relatorio.json", com_resumo: bool = True):
        super().__init__(com_resumo)
        self._destino = destino

    def criar_exportador(self) -> ExportadorRelatorio:
        return ExportadorJSON(self._destino)
