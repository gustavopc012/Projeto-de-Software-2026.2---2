import time
from abc import ABC, abstractmethod
from enum import Enum
import json
import csv
from api import obter_localizacao_cidade, buscar_previsao

class NivelRisco(Enum):
    NENHUM = "NENHUM"
    BAIXO = "BAIXO"
    MEDIO = "MÉDIO"
    ALTO = "ALTO"
    CRITICO = "CRÍTICO"

class LeituraClima:
    def __init__(self, cidade: str, temperatura: float, umidade: float, chuva: float):
        self._validar_dados(temperatura, umidade, chuva)

        self._cidade = cidade
        self._temperatura = float(temperatura)
        self._umidade = float(umidade)
        self._chuva = float(chuva) # Medida em mm

    # * RF1[E]: Dados climáticos protegidos. (Os dados climáticos obtidos da API jamais podem existir em estado inválido ou inconsistente.)
    def _validar_dados(self, temperatura: float, umidade: float, chuva: float) -> None:
        if temperatura is None or umidade is None or chuva is None:
            raise ValueError("Dado ausente na resposta da API")
        if temperatura < -50 or temperatura > 80:
            raise ValueError(f"Temperatura inválida ou ausente")
        if umidade == -999 or not (0 <= umidade <= 100):
            raise ValueError(f"Umidade fora do intervalo [0-100%]: {umidade}%")
        if chuva < 0:
            raise ValueError(f"Taxa de chuva inválida: {chuva} mm/h")

    @property # * RF2 [E] — Calculado, não atribuível.
    def cidade(self) -> str:
        return self._cidade
    
    @property
    def temperatura(self) -> float:
        return self._temperatura

    @property
    def umidade(self) -> float:
        return self._umidade

    @property
    def chuva(self) -> float:
        return self._chuva

    def __repr__(self):
        # Quando faz um print em um objeto da classe, mostra a mensagem 
        # * Ex.: maceio = LeituraClima("Maceió", 22.6, 85, 0)
        # * Ex.: print(maceio) // exibe <Maceió, 22.6°C, 85%, 0mm>
    
        return f"<{self._cidade}, {self._temperatura}°C, {self._umidade}%, {self._chuva}mm>"

# * RF3 [A/H]: Múltiplas categorias de alerta. -----------------------

class Alerta(ABC):
    # Classe Abstrata, serve de molde para as outras
    @property
    @abstractmethod
    def nome(self) -> str:
        pass

    @abstractmethod
    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        pass

    # * RF4 [P]: Alertas autodescritivos.
    @abstractmethod
    def mensagem_alerta(self, leitura: LeituraClima) -> str:
        pass
        
class AlertaCalor(Alerta):
    @property
    def nome(self) -> str:
        return "Calor extremo"
    
    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.temperatura >= 38 or (leitura.temperatura >= 32 and leitura.umidade >= 80):
            return NivelRisco.ALTO
        elif leitura.temperatura >= 32 or (leitura.temperatura >= 30 and leitura.umidade >= 70):
            return NivelRisco.MEDIO
        elif leitura.temperatura >= 28:
            return NivelRisco.BAIXO
        return NivelRisco.NENHUM
    
    def mensagem_alerta(self, leitura: LeituraClima) -> str:
        return f"⚠️ Alerta de calor: sensação térmica elevada com {leitura.temperatura}°C e umidade de {leitura.umidade}%, mantenha-se hidratado!"
    
class AlertaAlagamento(Alerta):
    @property
    def nome(self) -> str:
        return "Alagamento"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.chuva >= 30:
            return NivelRisco.CRITICO
        elif leitura.chuva >= 15:
            return NivelRisco.ALTO
        elif leitura.chuva >= 5:
            return NivelRisco.MEDIO
        elif leitura.chuva > 0:
            return NivelRisco.BAIXO
        return NivelRisco.NENHUM
    
    def mensagem_alerta(self, leitura: LeituraClima):
         return f"🌊 Alerta de alagamento: acúmulo de chuva de {leitura.chuva} mm/h em {leitura.cidade}, evite vias de risco!"

class AlertaGeada(Alerta):    
    @property
    def nome(self) -> str:
        return "Geada"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.temperatura <= 0:
            return NivelRisco.ALTO
        elif leitura.temperatura <= 4:
            return NivelRisco.MEDIO
        return NivelRisco.NENHUM
    
    def mensagem_alerta(self, leitura: LeituraClima):
        return f"❄️ Alerta de geada: temperatura crítica de {leitura.temperatura}°C em {leitura.cidade}, proteja hortas e animais!"
    
class AlertaTempestade(Alerta):
    @property
    def nome(self) -> str:
        return "Tempestade"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.chuva >= 20 and leitura.umidade >= 85:
            return NivelRisco.ALTO
        elif leitura.chuva >= 10:
            return NivelRisco.MEDIO
        return NivelRisco.NENHUM
    
    def mensagem_alerta(self, leitura: LeituraClima):
        return f"⛈️ Alerta de tempestade: chuva de {leitura.chuva} mm/h com umidade de {leitura.umidade}%, atenção a rajadas de vento e raios!"
    
class AlertaVento(Alerta):
    @property
    def nome(self) -> str:
        return "Vento"

    def avaliar_risco(self, leitura: LeituraClima) -> NivelRisco:
        if leitura.chuva >= 25 and leitura.umidade >= 80:
            return NivelRisco.ALTO
        elif leitura.chuva >= 15:
            return NivelRisco.MEDIO
        return NivelRisco.NENHUM

    
    def mensagem_alerta(self, leitura: LeituraClima):
        return f"🍃 Alerta de vento: rajadas prováveis com chuva de {leitura.chuva} mm/h."
 
# ! Provedores --------------------

class ProvedorClima(ABC):
    # Classe Abstrata, serve de molde para as outras
    @abstractmethod
    def obter_leitura(self, cidade) -> LeituraClima:
        pass
    
class ProvedorOpenMeteo(ProvedorClima):
    def obter_leitura(self, cidade: str) -> LeituraClima:
        lat, lon = obter_localizacao_cidade(cidade)
        dados = buscar_previsao(lat, lon)

        try:
            atual = dados["current"]
        except KeyError:
            raise ValueError("Resposta da API em formato inesperado")

        return LeituraClima(
            cidade=cidade,
            temperatura=atual.get("temperature_2m"),
            umidade=atual.get("relative_humidity_2m"),
            chuva=atual.get("rain"),
        )
    
class ProvedorFicticio(ProvedorClima):
    def obter_leitura(self, cidade: str) -> LeituraClima:
        return LeituraClima(
            cidade=cidade,
            temperatura=43.0,
            umidade=65.0,
            chuva=80.0,
        )

# * RF10 [E] — Cache transparente. Requisições repetidas para a mesma localidade em um
# * curto intervalo não devem sempre gerar nova chamada de rede, e isso deve ser invisível para o
# * código solicitante.

class ProvedorCache(ProvedorClima):
    def __init__(self, provedor_real: ProvedorClima, ttl_segundos: int = 300):
        self._provedor_real = provedor_real
        self._ttl = ttl_segundos
        self._cache = {}  # {cidade: (leitura_objeto, timestamp)}

    def obter_leitura(self, cidade: str) -> LeituraClima:
        agora = time.time()
        if cidade in self._cache:
            leitura, timestamp = self._cache[cidade]
            if agora - timestamp < self._ttl:
                return leitura
        
        nova_leitura = self._provedor_real.obter_leitura(cidade)
        self._cache[cidade] = (nova_leitura, agora)
        return nova_leitura

# ------------- PADRÃO 1: BUILDER (em ResultadoCidade) -------------
class ResultadoCidade:
    def __init__(self, builder: "ResultadoCidade.Builder"):
        self._cidade = builder.cidade
        self._leitura = builder.leitura
        self._alertas_ativos = list(builder.alertas_ativos)
        self._erro = builder.erro

    @property
    def cidade(self) -> str:
        return self._cidade

    @property
    def leitura(self) -> LeituraClima:
        return self._leitura
    @property
    def alertas_ativos(self) -> list:
        return self._alertas_ativos

    @property
    def erro(self) -> str:
        return self._erro

    class Builder:
        def __init__(self, cidade: str):
            if not cidade or not cidade.strip():
                raise ValueError("O nome da cidade é obrigatório.")
            self.cidade = cidade
            self.leitura = None
            self.alertas_ativos = []
            self.erro = ""

        def com_leitura(self, leitura: LeituraClima) -> "ResultadoCidade.Builder":
            self.leitura = leitura
            return self

        def com_alertas(self, alertas: list) -> "ResultadoCidade.Builder":
            self.alertas_ativos = list(alertas)
            return self

        def com_erro(self, mensagem_erro: str) -> "ResultadoCidade.Builder":
            self.erro = mensagem_erro
            return self

        def build(self) -> "ResultadoCidade":
            # Validação de consistência antes de o objeto existir
            if self.leitura is None and not self.erro:
                raise ValueError(f"Resultado inválido para '{self.cidade}': informe uma leitura ou um erro.")
            if self.leitura is not None and self.erro:
                raise ValueError(f"Resultado inconsistente para '{self.cidade}': não pode ter leitura e erro simultaneamente.")
            return ResultadoCidade(self)


# RF9 [A] — Múltiplos formatos de relatório.
# ------------- PADRÃO 2: FACTORY METHOD (nos Exportadores) -------------

# Product (Interface comum do produto criado)
class ExportadorRelatorio(ABC):
    @abstractmethod
    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        pass


# Concrete Products (Produtos Concretos)
class ExportadorConsole(ExportadorRelatorio):
    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        print("\n=== RELATÓRIO CLIMÁTICO ===")
        for res in resultados:
            if res.erro:
                print(f"{res.cidade}: ERRO -> {res.erro}")
            else:
                print(f"{res.cidade} ({res.leitura.temperatura}°C, {res.leitura.umidade}%, {res.leitura.chuva}mm/h)\n")
                for msg, n in res.alertas_ativos:
                    print(f"{n.value}: {msg}\n")
                if not res.alertas_ativos:
                    print("Sem Alertas Ativos")
            print("===========================")


class ExportadorCSV(ExportadorRelatorio):
    def __init__(self, destino: str = "relatorio.csv"):
        self._destino = destino

    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        with open(self._destino, "w", newline="", encoding="utf-8-sig") as file:
            escritor = csv.writer(file, delimiter=";")
            escritor.writerow(["Cidade", "Temperatura (°C)", "Umidade (%)", "Chuva (mm/h)", "Alertas ativos"])

            for res in resultados:
                if res.erro:
                    escritor.writerow([res.cidade, "", "", "", f"ERRO: {res.erro}"])
                else:
                    if res.alertas_ativos:
                        partes = [f"{desc} [{nivel.value}]" for desc, nivel in res.alertas_ativos]
                        texto = " | ".join(partes)
                    else:
                        texto = "Sem alertas"
                    escritor.writerow([res.cidade, res.leitura.temperatura, res.leitura.umidade, res.leitura.chuva, texto])
        print(f"\nRelatório CSV ('{self._destino}') gerado com sucesso!\n")


class ExportadorJSON(ExportadorRelatorio):
    def __init__(self, destino: str = "relatorio.json"):
        self._destino = destino

    def exportar(self, resultados: list[ResultadoCidade]) -> None:
        dados = []
        for res in resultados:
            if res.erro:
                dados.append({"cidade": res.cidade, "erro": res.erro})
            else:
                dados.append({
                    "cidade": res.cidade,
                    "temperatura": res.leitura.temperatura,
                    "umidade": res.leitura.umidade,
                    "chuva": res.leitura.chuva,
                    "alertas": [{"mensagem": msg, "nivel": nivel.value} for msg, nivel in res.alertas_ativos]
                })
        with open(self._destino, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        print(f"\nRelatório JSON ('{self._destino}') gerado com sucesso!\n")


# Creator (Declara o Factory Method e a lógica que usa o produto)
class GeradorRelatorioCreator(ABC):
    @abstractmethod
    def criar_exportador(self) -> ExportadorRelatorio:
        """Factory Method que as subclasses devem sobrescrever."""
        pass

    def gerar_relatorio(self, resultados: list[ResultadoCidade]) -> None:
        exportador = self.criar_exportador()
        exportador.exportar(resultados)


# Concrete Creators (Decidem qual classe concreta instanciar)
class GeradorConsoleCreator(GeradorRelatorioCreator):
    def criar_exportador(self) -> ExportadorRelatorio:
        return ExportadorConsole()


class GeradorCSVCreator(GeradorRelatorioCreator):
    def __init__(self, destino: str = "relatorio.csv"):
        self._destino = destino

    def criar_exportador(self) -> ExportadorRelatorio:
        return ExportadorCSV(self._destino)


class GeradorJSONCreator(GeradorRelatorioCreator):
    def __init__(self, destino: str = "relatorio.json"):
        self._destino = destino

    def criar_exportador(self) -> ExportadorRelatorio:
        return ExportadorJSON(self._destino)
