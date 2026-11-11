# 🌦️ Sistema de Alertas Meteorológicos Multifonte

Sistema em Python orientado a objetos que consulta as condições climáticas de várias localidades utilizando a API gratuita [Open-Meteo](https://open-meteo.com/). Ele avalia níveis de risco meteorológico e gera relatórios consolidados no terminal, em CSV e JSON.

O projeto utiliza padrões de projeto criacionais, estruturais e comportamentais para organizar a arquitetura, reduzir o acoplamento e facilitar a manutenção e a expansão do sistema.

## ▶️ Como executar

**Pré-requisitos:** Python 3.10 ou superior e conexão com a internet para consultar a API.

```bash
# 1. Entre na pasta do projeto
cd Projeto-de-Software-2026.2---2

# 2. Instale a única dependência externa
pip install requests

# 3. Execute o sistema
python main.py
```

**Menu disponível:**

| Opção | Ação |
|---|---|
| 1 | 📍 Relatório de uma cidade da lista (aceita o nome ou o número) |
| 2 | 🗺️ Relatório consolidado de todas as cidades no terminal |
| 3 | 📄 Exporta o relatório consolidado para `relatorio.csv` |
| 4 | 🧾 Exporta o relatório consolidado para `relatorio.json` |
| 5 | 🔎 Busca qualquer cidade pelo nome |
| 6 | 🔒 Demonstra a proteção dos dados (RF1, RF2 e RF4) |
| 7 | 🚪 Sair |

**Modo offline:** em `main.py`, troque `ProvedorOpenMeteo()` por `ProvedorFicticio()`. O sistema passa a utilizar dados fixos, permitindo demonstrar os níveis de alerta sem depender de conexão com a API.

**Cidades monitoradas:** edite a lista em `cidades.py`.

> **Observação:** as consultas são realizadas sob demanda, quando o usuário utiliza o sistema. Não há monitoramento contínuo em segundo plano.

## 🧪 Testes e demonstração

```bash
python demo_rf.py             # Demonstra os 10 requisitos em sequência
python -m unittest testes -v  # Executa os testes automatizados
```

A demonstração `demo_rf.py` utiliza dados simulados para apresentar os requisitos funcionais de maneira previsível, sem depender das condições climáticas reais.

Os testes automatizados utilizam respostas simuladas da API e não precisam de conexão com a internet. Eles cobrem os requisitos funcionais, incluindo:

- API inacessível e timeout;
- Cidade inexistente;
- JSON malformado, campos ausentes ou inválidos;
- Erros HTTP;
- Estrutura dos arquivos JSON e CSV exportados;
- Cache e expiração do TTL;
- Menu com entradas inválidas.

## 📁 Estrutura

| Arquivo | Conteúdo |
|---|---|
| `main.py` | Menu, avaliação uniforme dos alertas, coleta das cidades e tratamento de falhas |
| `classes.py` | Domínio (`LeituraClima`, alertas), provedores, Builder, exportadores, Factory Method, Proxy e Decorator |
| `api.py` | `OpenMeteoFacade`: acesso HTTP à Open-Meteo e validação do JSON recebido |
| `cidades.py` | Lista de localidades monitoradas |
| `observadores.py` | Interface Observer, observadores concretos e central de notificações |
| `testes.py` | Testes automatizados (`unittest`) |
| `demo_rf.py` | Roteiro de apresentação dos 10 requisitos |

## ✅ Requisitos funcionais

Cada requisito está marcado no código com um comentário `[RFx]`.

| Requisito | Onde está | Como foi atendido |
|---|---|---|
| RF1 [E] Dados climáticos protegidos | `LeituraClima.__init__` / `_validar` | Valida presença, tipo numérico, valores finitos e faixas físicas antes de criar o objeto. |
| RF2 [E] Calculado, não atribuível | `@property` de `LeituraClima`, `sensacao_termica`, `maior_risco` | Os atributos não possuem setter. A sensação térmica e o maior risco são calculados durante a leitura. |
| RF3 [A/H] Múltiplas categorias | `Alerta` e cinco subclasses | Calor, Alagamento, Geada, Tempestade e Vento, cada uma com critérios próprios sobre a mesma leitura. |
| RF4 [P] Alertas autodescritivos | `Alerta.__str__` | `print(alerta)` mostra o ícone, o nome e o critério de qualquer categoria. |
| RF5 [P] Avaliação uniforme | `avaliar_alertas_ativos` (`main.py`) | Um único laço polimórfico avalia as diferentes categorias de alerta. |
| RF6 [A/IF] Provedores intercambiáveis | `ProvedorClima` e implementações | Trocar o provedor no `main.py` não altera a lógica de avaliação dos alertas. |
| RF7 [C] Múltiplas localidades | `coletar_resultados`, `cidades.py` | Percorre todas as cidades e gera um único relatório consolidado. |
| RF8 [X] Falha graciosa | `coletar_resultados`, `OpenMeteoFacade._get_json`, `ProvedorOpenMeteo` | Trata falhas de rede, timeout, JSON malformado, cidade inexistente e erros ao salvar arquivos, permitindo a continuidade do sistema. |
| RF9 [A] Múltiplos formatos | Exportadores Console, CSV e JSON | O formato é escolhido pelo Factory Method, desacoplado da coleta dos dados. |
| RF10 [E] Cache transparente | `ProvedorCache` | Consultas repetidas à mesma cidade dentro de cinco minutos reutilizam os dados armazenados. A chave ignora maiúsculas e espaços. |

### Formato do JSON exportado

Todo item possui as mesmas chaves, tanto em caso de sucesso quanto de erro. Os alertas são ordenados do maior nível de gravidade para o menor.

```json
{
    "gerado_em": "2026-11-08T17:27:38",
    "total_cidades": 4,
    "resultados": [
        {
            "cidade": "Rio Largo",
            "status": "ok",
            "localidade": {
                "nome": "Rio Largo",
                "regiao": "Alagoas, Brasil"
            },
            "leitura": {
                "temperatura_c": 28.1,
                "sensacao_termica_c": 29.1,
                "umidade_pct": 70.0,
                "chuva_mm": 0.0,
                "vento_kmh": 19.4
            },
            "maior_risco": "BAIXO",
            "alertas": [
                {
                    "categoria": "Calor extremo",
                    "nivel": "BAIXO",
                    "mensagem": "Calor de 28.1°C ..."
                }
            ],
            "erro": null
        },
        {
            "cidade": "Atlantida",
            "status": "erro",
            "localidade": null,
            "leitura": null,
            "maior_risco": null,
            "alertas": [],
            "erro": "Localidade desconhecida: 'Atlantida'"
        }
    ]
}
```

---

## 🏗️ Padrões de projeto criacionais (Etapa 2)

### 1. Builder (`ResultadoCidade.Builder`)

- **Onde foi aplicado:** na construção dos objetos `ResultadoCidade`, em `classes.py`, utilizados por `coletar_resultados()` no `main.py`.

- **Problema no código original:** a classe `ResultadoCidade` precisava representar dois cenários diferentes: uma consulta realizada com sucesso ou uma falha durante a consulta. A construção por meio de um único construtor posicional exigia argumentos vazios ou nulos, dificultando a leitura e a manutenção do código.

- **Solução:** foi implementado um Builder interno com interface fluente, permitindo configurar gradualmente os dados do resultado por meio de métodos específicos.

**Demonstração do código utilizado:**

```python
class Builder:
    def __init__(self, cidade: str):
        self.cidade = cidade.strip()
        self.leitura = None
        self.alertas_ativos = []
        self.erro = ""

    def com_leitura(self, leitura):
        self.leitura = leitura
        return self

    def com_alertas(self, alertas):
        self.alertas_ativos = list(alertas)
        return self

    def com_erro(self, mensagem_erro):
        self.erro = mensagem_erro
        return self

    def build(self):
        if self.leitura is None and not self.erro:
            raise ValueError("Informe uma leitura ou um erro.")

        if self.leitura is not None and self.erro:
            raise ValueError("Leitura e erro ao mesmo tempo.")

        return ResultadoCidade(self)
```

**Utilização no `main.py`:**

```python
builder = ResultadoCidade.Builder(cidade)

try:
    leitura = provedor.obter_leitura(cidade)

    resultado = (
        builder
        .com_leitura(leitura)
        .com_alertas(
            avaliar_alertas_ativos(
                leitura, cidade, central_alertas
            )
        )
        .build()
    )

except ValueError as e:
    resultado = builder.com_erro(str(e)).build()
```

- **Por que escolhemos:** o Builder organiza a construção de objetos que possuem diferentes possibilidades de preenchimento. Ele centraliza as validações e garante que um resultado não tenha leitura e erro simultaneamente, nem fique sem os dois.

### 2. Factory Method (`GeradorRelatorioCreator`)

- **Onde foi aplicado:** na geração dos relatórios do RF9, utilizando `GeradorConsoleCreator`, `GeradorCSVCreator` e `GeradorJSONCreator`.

- **Problema no código original:** o código principal precisava conhecer diretamente as classes concretas dos exportadores para escolher e instanciar cada formato. Isso concentrava a responsabilidade de criação no cliente.

- **Solução:** foi criada a classe abstrata `GeradorRelatorioCreator`, que define o método `criar_exportador()`. Cada Creator concreto implementa esse método e decide qual exportador será criado.

**Demonstração do código utilizado:**

```python
class GeradorRelatorioCreator(ABC):

    @abstractmethod
    def criar_exportador(self):
        pass

    def gerar_relatorio(self, resultados):
        exportador = self.criar_exportador()

        if self._com_resumo:
            exportador = ExportadorComResumo(exportador)

        exportador.exportar(resultados)


class GeradorConsoleCreator(GeradorRelatorioCreator):

    def criar_exportador(self):
        return ExportadorConsole()


class GeradorCSVCreator(GeradorRelatorioCreator):

    def criar_exportador(self):
        return ExportadorCSV(self._destino)


class GeradorJSONCreator(GeradorRelatorioCreator):

    def criar_exportador(self):
        return ExportadorJSON(self._destino)
```

**Utilização no `main.py`:**

```python
criadores_consolidados = {
    "2": GeradorConsoleCreator(),
    "3": GeradorCSVCreator("relatorio.csv"),
    "4": GeradorJSONCreator("relatorio.json"),
}
```

- **Por que escolhemos:** o Factory Method separa a criação dos objetos da lógica que utiliza os relatórios. Assim, novos formatos podem ser adicionados por meio de novos Creators, sem concentrar a instanciação dos exportadores no código principal.

---

## 🧱 Padrões de projeto estruturais (Etapa 3)

### 1. Facade (`OpenMeteoFacade` em `api.py`)

- **Problema:** consultar o clima exige diferentes operações HTTP. Primeiro é necessário realizar a geocodificação para obter latitude e longitude da cidade; depois, utilizar essas coordenadas para consultar as informações meteorológicas. Também é necessário tratar as respostas JSON.

- **Solução:** a classe `OpenMeteoFacade` centraliza as operações por meio do método `obter_clima_completo(cidade)`, escondendo os detalhes das requisições externas.

**Demonstração do código utilizado:**

```python
class OpenMeteoFacade:

    def obter_clima_completo(self, cidade: str) -> dict:

        # Passo 1: descobrir latitude e longitude
        dados_geo = self._get_json(
            self.GEO_URL,
            {
                "name": cidade,
                "count": 1,
                "language": "pt",
                "format": "json"
            },
            "geocodificação",
        )

        resultados = dados_geo.get("results") or []

        if not resultados:
            raise ValueError(
                f"Localidade desconhecida: '{cidade}'"
            )

        local = resultados[0]
        lat, lon = local.get("latitude"), local.get("longitude")

        # Passo 2: buscar o clima atual
        dados_clima = self._get_json(
            self.WEATHER_URL,
            {
                "latitude": lat,
                "longitude": lon,
                "current": self.CAMPOS_ATUAIS
            },
            "previsão",
        )

        return {
            "localidade": {
                "nome": local.get("name") or cidade,
                "estado": local.get("admin1") or "",
                "pais": local.get("country") or "",
            },
            "current": dados_clima.get("current"),
        }
```

- **Por que escolhemos:** o Facade oferece uma interface simplificada para acessar um subsistema complexo. As outras classes não precisam conhecer os detalhes das URLs, parâmetros, geocodificação e requisições HTTP.

### 2. Adapter (`ProvedorOpenMeteo` em `classes.py`)

- **Problema:** a API Open-Meteo retorna informações em formato JSON, enquanto o domínio do sistema utiliza objetos próprios e validados, como `LeituraClima`.

- **Solução:** a classe `ProvedorOpenMeteo` implementa a interface `ProvedorClima`, utiliza a `OpenMeteoFacade` e converte os dados externos em um objeto `LeituraClima`.

**Demonstração do código utilizado:**

```python
class ProvedorOpenMeteo(ProvedorClima):

    def __init__(self, facade=None):
        self._facade = facade or OpenMeteoFacade()

    def obter_leitura(self, cidade: str) -> LeituraClima:

        dados = self._facade.obter_clima_completo(cidade)

        atual = dados.get("current")
        local = dados.get("localidade") or {}

        regiao = ", ".join(
            p for p in (local.get("estado"), local.get("pais"))
            if p
        )

        return LeituraClima(
            cidade=local.get("nome") or cidade,
            regiao=regiao,
            temperatura=atual.get("temperature_2m"),
            umidade=atual.get("relative_humidity_2m"),
            chuva=atual.get("rain"),
            vento=atual.get("wind_speed_10m"),
        )
```

- **Por que escolhemos:** o Adapter resolve a incompatibilidade entre a estrutura externa da API e a interface esperada pelo sistema. Dessa forma, o restante da aplicação trabalha somente com objetos `LeituraClima`, sem depender diretamente do JSON original.

### 3. Proxy (`ProvedorCache` em `classes.py`)

- **Problema:** chamadas repetidas à API para consultar a mesma cidade podem aumentar o tempo de execução e gerar requisições desnecessárias.

- **Solução:** foi implementado um Caching Proxy com a mesma interface `ProvedorClima`. Antes de consultar o provedor real, ele verifica se existe uma leitura válida armazenada na memória.

**Demonstração do código utilizado:**

```python
class ProvedorCache(ProvedorClima):

    def __init__(self, provedor_real, ttl_segundos=300):
        self._provedor_real = provedor_real
        self._ttl = ttl_segundos
        self._cache = {}

    def obter_leitura(self, cidade: str) -> LeituraClima:

        chave = cidade.strip().casefold()
        agora = time.monotonic()

        if chave in self._cache:
            leitura, instante = self._cache[chave]

            if agora - instante < self._ttl:
                return leitura

        leitura = self._provedor_real.obter_leitura(cidade)
        self._cache[chave] = (leitura, agora)

        return leitura
```

**Utilização no `main.py`:**

```python
provedor_base: ProvedorClima = ProvedorOpenMeteo()

provedor: ProvedorClima = ProvedorCache(
    provedor_base,
    ttl_segundos=300
)
```

- **Por que escolhemos:** o Proxy controla o acesso ao provedor real e permite reutilizar resultados recentes sem modificar a lógica que solicita os dados climáticos. O cache tem validade de cinco minutos e atende ao RF10.

### 4. Decorator (`ExportadorComResumo` em `classes.py`)

- **Problema:** os diferentes exportadores precisam apresentar informações de resumo, como total de cidades, quantidade de alertas, erros e maior risco encontrado. Implementar essa lógica separadamente em cada exportador provocaria duplicação de código.

- **Solução:** a classe `ExportadorComResumo` implementa a mesma interface `ExportadorRelatorio`, envolve um exportador existente e acrescenta a apresentação do resumo após a exportação original.

**Demonstração do código utilizado:**

```python
class ExportadorComResumo(ExportadorRelatorio):

    def __init__(self, exportador: ExportadorRelatorio):
        self._exportador = exportador

    def exportar(self, resultados):

        # Executa a exportação original
        self._exportador.exportar(resultados)

        # Acrescenta o resumo
        self._imprimir_resumo(resultados)

    @staticmethod
    def _imprimir_resumo(resultados):

        ok = [r for r in resultados if not r.erro]
        com_alerta = [r for r in ok if r.alertas_ativos]
        erros = len(resultados) - len(ok)

        maior = max(
            (r.maior_risco for r in ok),
            key=lambda n: n.peso,
            default=NivelRisco.NENHUM
        )

        print(
            f"Resumo: {len(resultados)} cidades · "
            f"{len(com_alerta)} com alerta · "
            f"{erros} com erro · "
            f"maior risco: {maior}"
        )
```

- **Por que escolhemos:** o Decorator permite adicionar responsabilidades aos objetos por composição, sem alterar as classes originais ou criar subclasses específicas para cada formato de relatório. O mesmo decorador funciona com Console, CSV e JSON.

- **Diferença em relação ao Proxy:** ambos envolvem objetos que possuem interfaces compatíveis. Entretanto, o Proxy controla o acesso ao objeto original, enquanto o Decorator acrescenta responsabilidades ao comportamento do objeto envolvido.

---

## 🔔 Padrões de projeto comportamentais (Etapa 4)

### 1. Observer (`CentralNotificacoes` em `observadores.py`)

- **Onde foi aplicado:** no gerenciamento das notificações de risco climático, utilizando a interface `ObservadorRisco`, os observadores concretos `DefesaCivilNotifier` e `LogAuditoria`, e a classe `CentralNotificacoes`.

- **Problema:** a identificação de riscos climáticos pode exigir diferentes ações, como registrar eventos severos e emitir notificações. Se a lógica de análise precisasse chamar diretamente cada mecanismo de resposta, ficaria acoplada aos componentes de notificação. A inclusão de novos mecanismos também exigiria alterações na lógica principal.

- **Solução:** foi implementada uma interface abstrata `ObservadorRisco`, que define o método `atualizar()`. Os observadores concretos implementam suas próprias responsabilidades, enquanto a `CentralNotificacoes` gerencia as inscrições e distribui os eventos.

**Demonstração do código utilizado — `observadores.py`:**

```python
# Interface base do Observer
class ObservadorRisco(ABC):

    @abstractmethod
    def atualizar(self, cidade: str, alerta: str, nivel_risco: str):
        pass


# Observer concreto: Defesa Civil
class DefesaCivilNotifier(ObservadorRisco):

    def atualizar(self, cidade: str, alerta: str, nivel_risco: str):

        if nivel_risco == "CRITICO":
            print(
                f"[DEFESA CIVIL NOTIFICADA] "
                f"Equipes despachadas para {cidade}!"
            )


# Observer concreto: auditoria
class LogAuditoria(ObservadorRisco):

    def atualizar(self, cidade: str, alerta: str, nivel_risco: str):

        if nivel_risco in ["ALTO", "CRITICO"]:
            print(
                f"[LOG AUDITORIA] Evento severo registrado "
                f"em {cidade}: {alerta} ({nivel_risco})"
            )


# Subject: central de notificações
class CentralNotificacoes:

    def __init__(self):
        self._inscritos = []

    def inscrever(self, observador: ObservadorRisco):
        if observador not in self._inscritos:
            self._inscritos.append(observador)

    def cancelar(self, observador: ObservadorRisco):
        if observador in self._inscritos:
            self._inscritos.remove(observador)

    def notificar_todos(self, cidade, alerta, nivel_risco):
        for observador in self._inscritos:
            observador.atualizar(cidade, alerta, nivel_risco)
```

**Inscrição dos observadores no `main.py`:**

```python
central_alertas = CentralNotificacoes()

central_alertas.inscrever(DefesaCivilNotifier())
central_alertas.inscrever(LogAuditoria())
```

**Disparo das notificações durante a avaliação dos riscos:**

```python
if nivel in (NivelRisco.ALTO, NivelRisco.CRITICO):
    central_alertas.notificar_todos(
        cidade,
        alerta.nome,
        nivel.name
    )
```

- **Por que escolhemos:** o Observer permite desacoplar a identificação dos riscos das ações executadas em resposta a eles. Novos observadores podem ser adicionados sem exigir alterações na lógica principal de análise climática.

**Comportamento dos observadores:**

- `DefesaCivilNotifier`: simula uma notificação à Defesa Civil somente quando o risco é CRÍTICO.
- `LogAuditoria`: registra eventos classificados como ALTO ou CRÍTICO.

**Observação:** a comunicação com a Defesa Civil é simulada no terminal. O projeto não possui integração real com órgãos externos.

**Fluxo de funcionamento:**

1. O sistema consulta as condições climáticas de uma cidade.
2. Os alertas avaliam o nível de risco identificado.
3. Quando o risco é ALTO ou CRÍTICO, a `CentralNotificacoes` é acionada.
4. A central percorre os observadores inscritos e chama o método `atualizar()`.
5. Cada observador executa sua própria responsabilidade, conforme o nível de risco recebido.

---

## 👥 Integrantes

- Gabriel Fernandes Costa Macena
- Gabriel Jatobá
- Gustavo Pereira Cordeiro

**Disciplina:** Projeto de Software  
**Período:** 2026.2
