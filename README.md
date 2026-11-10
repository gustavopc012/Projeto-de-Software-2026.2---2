# 🌦️ Sistema de Alertas Meteorológicos Multifonte

Sistema em Python orientado a objetos que monitora as condições climáticas de várias localidades em tempo real, usando a API gratuita [Open-Meteo](https://open-meteo.com/). Ele avalia níveis de risco meteorológico e gera relatórios consolidados no terminal, em CSV e em JSON.

## ▶️ Como executar

**Pré-requisitos:** Python 3.10+ e conexão com a internet (ou o modo offline, explicado abaixo).

```bash
# 1. Entre na pasta do projeto
cd Projeto-de-Software-2026.2---2

# 2. Instale a única dependência externa
pip install requests

# 3. Execute o sistema
python main.py
```

Menu disponível:

| Opção | Ação |
|---|---|
| 1 | 📍 Relatório de uma cidade da lista (aceita o nome ou o número) |
| 2 | 🗺️ Relatório consolidado de todas as cidades no terminal |
| 3 | 📄 Exporta o relatório consolidado para `relatorio.csv` |
| 4 | 🧾 Exporta o relatório consolidado para `relatorio.json` |
| 5 | 🔎 Busca qualquer cidade pelo nome |
| 6 | 🔒 Demonstra a proteção dos dados (RF1, RF2 e RF4) |
| 7 | 🚪 Sair |

**Modo offline:** em `main.py`, troque `ProvedorOpenMeteo()` por `ProvedorFicticio()`. O sistema passa a usar dados fixos, o que é útil para apresentar todos os níveis de alerta sem depender do clima real.

**Cidades monitoradas:** edite a lista em `cidades.py`.

## 🧪 Testes e demonstração

```bash
python demo_rf.py              # demonstra os 10 requisitos em sequência (offline, resultado sempre igual)
python -m unittest testes -v   # testes automatizados
```

O documento `Requisitos_e_Padroes.pdf` resume os requisitos, os casos de teste (com a saída real do `demo_rf.py`) e explica os padrões de projeto.

São 22 testes automatizados, que não precisam de internet porque as respostas da API são simuladas. Eles cobrem os 10 requisitos, incluindo:

- API inacessível e *timeout*;
- cidade inexistente;
- JSON malformado (corpo que não é JSON, lista no lugar de objeto, campos ausentes ou com texto, falta do bloco `current`);
- erro HTTP 4xx;
- estrutura do JSON e do CSV exportados;
- cache e expiração do TTL;
- menu com entradas inválidas.

## 📁 Estrutura

| Arquivo | Conteúdo |
|---|---|
| `main.py` | Menu, avaliação uniforme dos alertas, coleta das cidades e tratamento de falhas |
| `classes.py` | Domínio (`LeituraClima`, alertas), provedores, Builder, exportadores, Factory Method e Decorator |
| `api.py` | `OpenMeteoFacade`: acesso HTTP à Open-Meteo e validação do JSON recebido |
| `cidades.py` | Lista de localidades monitoradas |
| `testes.py` | Testes automatizados (`unittest`) |
| `demo_rf.py` | Roteiro de apresentação dos 10 requisitos |

## ✅ Requisitos funcionais

Cada requisito está marcado no código com um comentário `[RFx]`.

| Requisito | Onde está | Como foi atendido |
|---|---|---|
| **RF1 [E]** Dados climáticos protegidos | `LeituraClima.__init__` / `_validar` | Valida presença, tipo numérico, valores finitos e faixas físicas antes de o objeto existir. Uma leitura inválida nunca é criada. |
| **RF2 [E]** Calculado, não atribuível | `@property` de `LeituraClima`, `sensacao_termica`, `maior_risco` | Os atributos não têm *setter*. A sensação térmica e o maior risco são calculados na hora da leitura. |
| **RF3 [A/H]** Múltiplas categorias | `Alerta` e 5 subclasses | Calor, Alagamento, Geada, Tempestade e Vento, cada uma com critério próprio sobre a mesma leitura. |
| **RF4 [P]** Alertas autodescritivos | `Alerta.__str__` | `print(alerta)` mostra o ícone, o nome e o critério de qualquer categoria. |
| **RF5 [P]** Avaliação uniforme | `avaliar_alertas_ativos` (`main.py`) | Um único laço polimórfico, sem `if` nem `isinstance` por tipo. |
| **RF6 [A/IF]** Provedores intercambiáveis | `ProvedorClima` e implementações | Trocar o provedor no `main.py` não altera a lógica de alertas. |
| **RF7 [C]** Múltiplas localidades | `coletar_resultados`, `cidades.py` | Percorre todas as cidades e gera um único relatório consolidado. |
| **RF8 [X]** Falha graciosa | `coletar_resultados`, `OpenMeteoFacade._get_json`, `ProvedorOpenMeteo` | Rede fora, *timeout*, JSON malformado, cidade inexistente e erro ao salvar o arquivo viram mensagens de erro, e o sistema continua rodando. |
| **RF9 [A]** Múltiplos formatos | Exportadores Console, CSV e JSON | O formato é escolhido pelo Factory Method, desacoplado da coleta dos dados. |
| **RF10 [E]** Cache transparente | `ProvedorCache` | Consultas repetidas à mesma cidade dentro de 5 minutos não acessam a rede. A chave ignora maiúsculas e espaços. |

### Formato do JSON exportado

Todo item tem as mesmas chaves, tanto em caso de sucesso quanto de erro. Os alertas vêm ordenados do mais grave para o menos grave.

```json
{
    "gerado_em": "2026-11-08T17:27:38",
    "total_cidades": 4,
    "resultados": [
        {
            "cidade": "Rio Largo",
            "status": "ok",
            "localidade": { "nome": "Rio Largo", "regiao": "Alagoas, Brasil" },
            "leitura": {
                "temperatura_c": 28.1, "sensacao_termica_c": 29.1,
                "umidade_pct": 70.0, "chuva_mm": 0.0, "vento_kmh": 19.4
            },
            "maior_risco": "BAIXO",
            "alertas": [
                { "categoria": "Calor extremo", "nivel": "BAIXO", "mensagem": "Calor de 28.1°C ..." }
            ],
            "erro": null
        },
        {
            "cidade": "Atlantida", "status": "erro", "localidade": null, "leitura": null,
            "maior_risco": null, "alertas": [], "erro": "Localidade desconhecida: 'Atlantida'"
        }
    ]
}
```

---

## 🏗️ Padrões de projeto criacionais (Etapa 2)

### 1. Builder (`ResultadoCidade.Builder`)

* **Onde foi aplicado:** na construção dos objetos imutáveis `ResultadoCidade` (em `classes.py`, usado em `coletar_resultados()` no `main.py`).
* **Problema no código original:** a classe `ResultadoCidade` representava dois cenários (leitura com sucesso ou falha graciosa do RF8) com um único construtor posicional. Isso obrigava o cliente a passar argumentos vazios ou nulos, como em `ResultadoCidade(cidade, None, [], str(e))`.
* **Solução:** um `Builder` interno com interface fluente (`.com_leitura()`, `.com_alertas()`, `.com_erro()`, `.build()`). Ele elimina os parâmetros nulos, mantém `ResultadoCidade` imutável e centraliza a validação no `build()`. Assim, um resultado nunca tem leitura e erro ao mesmo tempo, nem fica sem nenhum dos dois.

### 2. Factory Method (`GeradorRelatorioCreator`)

* **Onde foi aplicado:** na geração de relatórios do RF9 (`GeradorConsoleCreator`, `GeradorCSVCreator` e `GeradorJSONCreator`).
* **Problema no código original:** o `main.py` instanciava diretamente os exportadores concretos dentro de blocos `if/elif`.
* **Solução:** a classe abstrata `GeradorRelatorioCreator` declara o Factory Method `criar_exportador()`, e cada formato tem seu próprio Creator concreto. Para criar um novo formato (PDF, HTML), basta criar uma nova subclasse, sem mexer no `main.py`.

---

## 🧱 Padrões de projeto estruturais (Etapa 3)

### 1. Facade (`OpenMeteoFacade` em `api.py`)

* **Problema:** consultar o clima exige duas chamadas HTTP (a geocodificação, que transforma o nome em latitude/longitude, e depois a previsão), além do tratamento do JSON de cada uma.
* **Solução:** um único método, `obter_clima_completo(cidade)`, orquestra as duas chamadas. Ele também valida o JSON recebido (`_get_json`) e devolve sempre um dicionário no mesmo formato.
* **Por que escolhemos:** o Facade oferece uma porta de entrada simples para um subsistema complicado. URLs, parâmetros e erros HTTP ficam isolados em um só lugar.

### 2. Adapter (`ProvedorOpenMeteo` em `classes.py`)

* **Problema:** o domínio trabalha com objetos validados (`LeituraClima`), mas a API devolve um dicionário cru, com chaves como `temperature_2m` e `relative_humidity_2m`.
* **Solução:** um Adapter de objeto que implementa a interface `ProvedorClima` (Target), envolve o Facade (Adaptee) e traduz o JSON para `LeituraClima`.
* **Por que escolhemos:** ele resolve a incompatibilidade de interfaces e concentra o acoplamento com a API em uma única classe.

### 3. Proxy (`ProvedorCache` em `classes.py`, que atende o RF10)

* **Problema:** chamadas repetidas à API gastam banda, atrasam a execução e podem esbarrar em *rate limits*.
* **Solução:** um Caching Proxy com a mesma interface `ProvedorClima`. Se a cidade estiver no cache dentro do TTL, ele responde da memória; se não, delega ao provedor real.
* **Por que escolhemos:** o Proxy controla o acesso ao objeto real sem que o cliente perceba, exatamente como o RF10 exige.

### 4. Decorator (`ExportadorComResumo` em `classes.py`)

* **Problema:** queríamos exibir um resumo do relatório (total de cidades, quantas têm alerta, quantas deram erro e o maior risco encontrado) depois de **qualquer** exportação. Fazer isso dentro de cada exportador duplicaria código. Criar subclasses (`ExportadorCSVComResumo`, `ExportadorJSONComResumo`...) multiplicaria as classes.
* **Solução:** `ExportadorComResumo` implementa a mesma interface `ExportadorRelatorio` e **envolve** outro exportador. Ele repassa a chamada `exportar()` ao objeto decorado e depois acrescenta o resumo. O decorador é aplicado em `GeradorRelatorioCreator.gerar_relatorio()` sempre que o Creator é criado com `com_resumo=True`, que é o padrão.
* **Por que escolhemos:** o Decorator adiciona responsabilidade a um objeto por composição, em tempo de execução, sem alterar as classes existentes (princípio aberto/fechado). O mesmo decorador funciona com Console, CSV e JSON, e com qualquer formato futuro.
* **Diferença em relação ao Proxy:** os dois envolvem um objeto com a mesma interface. O Proxy **controla o acesso** ao objeto real (pode nem chamá-lo, como no cache). O Decorator **sempre delega** e **acrescenta comportamento**.


