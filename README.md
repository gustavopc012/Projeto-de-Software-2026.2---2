# 🌦️ Sistema de Alertas Meteorológicos Multifonte

Sistema desenvolvido em Python, utilizando programação orientada a objetos, para consultar condições climáticas de diferentes localidades por meio da API gratuita [Open-Meteo](https://open-meteo.com/). O sistema avalia níveis de risco meteorológico e gera relatórios consolidados no terminal, em CSV e JSON.

A aplicação utiliza diferentes padrões de projeto para organizar suas responsabilidades, reduzir o acoplamento entre componentes e facilitar a manutenção e a expansão do código.

## ▶️ Como executar

**Pré-requisitos:** Python 3.10 ou superior e conexão com a internet para utilizar a API Open-Meteo.

```bash
# 1. Entre na pasta do projeto
cd Projeto-de-Software-2026.2---2

# 2. Instale a dependência externa
pip install requests

# 3. Execute o sistema
python main.py
```

### Menu disponível

| Opção | Ação |
|---|---|
| 1 | 📍 Relatório de uma cidade da lista (aceita o nome ou o número) |
| 2 | 🗺️ Relatório consolidado de todas as cidades no terminal |
| 3 | 📄 Exporta o relatório consolidado para `relatorio.csv` |
| 4 | 🧾 Exporta o relatório consolidado para `relatorio.json` |
| 5 | 🔎 Busca qualquer cidade pelo nome |
| 6 | 🔒 Demonstra a proteção dos dados (RF1, RF2 e RF4) |
| 7 | 🚪 Sair |

**Modo offline:** em `main.py`, substitua `ProvedorOpenMeteo()` por `ProvedorFicticio()`. O sistema utilizará dados fixos, permitindo demonstrar os níveis de alerta sem depender de uma conexão com a API externa.

**Cidades monitoradas:** a lista de localidades pode ser editada em `cidades.py`.

> **Observação:** o sistema realiza consultas quando solicitado pelo usuário. Não possui monitoramento meteorológico contínuo em segundo plano.

## 🧪 Testes e demonstração

Para executar a demonstração dos requisitos funcionais:

```bash
python demo_rf.py
```

Para executar os testes automatizados:

```bash
python -m unittest testes -v
```

A demonstração `demo_rf.py` apresenta os dez requisitos funcionais em sequência, utilizando dados simulados para permitir uma execução previsível, sem depender de condições climáticas reais.

Os testes automatizados utilizam respostas simuladas da API, dispensando conexão com a internet. Eles abrangem situações como:

- API inacessível e timeout;
- Cidade inexistente;
- JSON malformado, campos ausentes e tipos inválidos;
- Erros HTTP 4xx;
- Estrutura dos arquivos JSON e CSV exportados;
- Funcionamento do cache e expiração do TTL;
- Entradas inválidas no menu.

## 📁 Estrutura do projeto

| Arquivo | Conteúdo |
|---|---|
| `main.py` | Menu principal, avaliação dos alertas, coleta das cidades e tratamento de falhas |
| `classes.py` | Classes de domínio, leitura climática, alertas, provedores, Builder, Factory Method, exportadores, Adapter, Proxy e Decorator |
| `api.py` | Implementação da `OpenMeteoFacade`, responsável pelo acesso HTTP à Open-Meteo e validação das respostas |
| `cidades.py` | Lista de localidades monitoradas |
| `observadores.py` | Implementação do padrão Observer, com interface, observadores concretos e central de notificações |
| `testes.py` | Testes automatizados utilizando `unittest` |
| `demo_rf.py` | Demonstração dos dez requisitos funcionais |

## ✅ Requisitos funcionais

Cada requisito está identificado no código por meio de comentários `[RFx]`.

| Requisito | Onde está | Como foi atendido |
|---|---|---|
| RF1 [E] Dados climáticos protegidos | `LeituraClima.__init__` / `_validar` | Valida presença, tipo numérico, valores finitos e faixas físicas antes de criar o objeto. |
| RF2 [E] Calculado, não atribuível | `@property` de `LeituraClima`, `sensacao_termica`, `maior_risco` | Os atributos não possuem setter. A sensação térmica e o maior risco são calculados durante a leitura. |
| RF3 [A/H] Múltiplas categorias | `Alerta` e cinco subclasses | Implementa as categorias Calor, Alagamento, Geada, Tempestade e Vento, cada uma com seu próprio critério. |
| RF4 [P] Alertas autodescritivos | `Alerta.__str__` | A representação textual apresenta o ícone, o nome e o critério de cada categoria. |
| RF5 [P] Avaliação uniforme | `avaliar_alertas_ativos` (`main.py`) | Utiliza um único laço polimórfico para avaliar as categorias de alerta. |
| RF6 [A/IF] Provedores intercambiáveis | `ProvedorClima` e implementações | Permite substituir o provedor climático sem modificar a lógica de avaliação dos alertas. |
| RF7 [C] Múltiplas localidades | `coletar_resultados`, `cidades.py` | Percorre as cidades cadastradas e gera um relatório consolidado. |
| RF8 [X] Falha graciosa | `coletar_resultados`, `OpenMeteoFacade._get_json`, `ProvedorOpenMeteo` | Trata falhas de rede, timeout, JSON inválido, cidade inexistente e erros durante a gravação dos arquivos, permitindo a continuidade do sistema. |
| RF9 [A] Múltiplos formatos | Exportadores Console, CSV e JSON | Permite gerar relatórios em diferentes formatos por meio do Factory Method. |
| RF10 [E] Cache transparente | `ProvedorCache` | Reutiliza consultas da mesma cidade durante cinco minutos, evitando novas requisições à API. A chave do cache desconsidera maiúsculas e espaços. |

## 📄 Formato do JSON exportado

O relatório JSON mantém uma estrutura padronizada para os resultados, tanto em casos de sucesso quanto de erro. Os alertas são organizados do maior nível de gravidade para o menor.

Exemplo ilustrativo:

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

- **Onde foi aplicado:** na construção dos objetos imutáveis `ResultadoCidade`, em `classes.py`, utilizados por `coletar_resultados()` no `main.py`.
- **Problema no código original:** a classe `ResultadoCidade` representava dois cenários — consulta bem-sucedida ou falha graciosa do RF8 — por meio de um único construtor posicional. Isso obrigava o cliente a passar argumentos vazios ou nulos, como `ResultadoCidade(cidade, None, [], str(e))`.
- **Solução:** foi implementado um Builder interno com interface fluente (`.com_leitura()`, `.com_alertas()`, `.com_erro()` e `.build()`). Ele elimina a necessidade de parâmetros nulos, mantém o objeto imutável e centraliza a validação durante a construção.
- **Por que escolhemos:** o Builder organiza a criação de objetos com diferentes possibilidades de preenchimento, garantindo a consistência do resultado antes de sua finalização.

### 2. Factory Method (`GeradorRelatorioCreator`)

- **Onde foi aplicado:** na criação dos exportadores de relatórios do RF9, por meio de `GeradorConsoleCreator`, `GeradorCSVCreator` e `GeradorJSONCreator`.
- **Problema no código original:** o `main.py` instanciava diretamente os exportadores concretos, concentrando a escolha e a criação dos formatos na lógica principal.
- **Solução:** a classe abstrata `GeradorRelatorioCreator` declara o método `criar_exportador()`, enquanto cada Creator concreto decide qual exportador será instanciado.
- **Por que escolhemos:** o Factory Method separa a criação dos objetos de sua utilização, facilitando a inclusão de novos formatos de relatório sem concentrar a lógica de instanciação no código cliente.

---

## 🧱 Padrões de projeto estruturais (Etapa 3)

### 1. Facade (`OpenMeteoFacade` em `api.py`)

- **Problema:** consultar o clima exige duas operações HTTP: a geocodificação, que transforma o nome da cidade em coordenadas, e a consulta meteorológica. Também é necessário tratar as respostas JSON de cada operação.
- **Solução:** o método `obter_clima_completo(cidade)` centraliza e organiza essas operações. A classe também valida o JSON recebido por meio de `_get_json` e disponibiliza os dados em uma estrutura padronizada.
- **Por que escolhemos:** o Facade oferece uma interface simplificada para acessar um subsistema mais complexo, isolando URLs, parâmetros e tratamento de erros.

### 2. Adapter (`ProvedorOpenMeteo` em `classes.py`)

- **Problema:** o domínio trabalha com objetos validados (`LeituraClima`), enquanto a API externa retorna dados em um dicionário JSON, com chaves como `temperature_2m` e `relative_humidity_2m`.
- **Solução:** `ProvedorOpenMeteo` implementa a interface `ProvedorClima`, utiliza a Facade para consultar a API e converte a resposta externa em um objeto `LeituraClima`.
- **Por que escolhemos:** o Adapter resolve a incompatibilidade entre a estrutura externa e a interface esperada pelo sistema, mantendo o restante da aplicação independente do formato original da API.

### 3. Proxy (`ProvedorCache` em `classes.py`, responsável pelo RF10)

- **Problema:** chamadas repetidas à API podem aumentar o tempo de execução, consumir recursos de rede e gerar requisições desnecessárias.
- **Solução:** foi implementado um Caching Proxy com a mesma interface `ProvedorClima`. Quando existe uma leitura válida no cache, ela é reutilizada; caso contrário, a consulta é encaminhada ao provedor original e o resultado é armazenado.
- **Por que escolhemos:** o Proxy controla o acesso ao provedor real e permite implementar o cache de maneira transparente, sem modificar a lógica que utiliza o serviço climático.

### 4. Decorator (`ExportadorComResumo` em `classes.py`)

- **Problema:** diferentes formatos de relatório precisam apresentar informações de resumo, como total de cidades, quantidade de alertas, erros e maior risco encontrado. Implementar essa lógica separadamente em cada exportador provocaria duplicação de código.
- **Solução:** `ExportadorComResumo` implementa a mesma interface `ExportadorRelatorio`, envolve outro exportador e acrescenta o resumo ao comportamento original. O decorador é aplicado pelo `GeradorRelatorioCreator.gerar_relatorio()` quando `com_resumo=True`, que é o padrão.
- **Por que escolhemos:** o Decorator permite adicionar responsabilidades a objetos por composição, sem modificar diretamente as classes originais. O mesmo decorador pode ser utilizado com os exportadores Console, CSV e JSON.
- **Diferença em relação ao Proxy:** ambos envolvem objetos que possuem uma interface compatível. Entretanto, o Proxy controla o acesso ao objeto original, enquanto o Decorator acrescenta responsabilidades ao comportamento do objeto envolvido.

---

## 🔔 Padrões de projeto comportamentais (Etapa 4)

### 1. Observer (`CentralNotificacoes` em `observadores.py`)

- **Onde foi aplicado:** no gerenciamento das notificações de risco climático, utilizando a interface `ObservadorRisco`, os observadores concretos `DefesaCivilNotifier` e `LogAuditoria`, e a classe `CentralNotificacoes`.
- **Problema no código original:** a identificação de riscos climáticos pode exigir diferentes ações, como registrar eventos severos e emitir notificações. Se a lógica de análise precisasse chamar diretamente cada mecanismo de resposta, ficaria fortemente acoplada aos componentes de notificação. A inclusão de novos mecanismos também exigiria alterações na lógica principal.
- **Solução:** a classe `ObservadorRisco` define a interface `atualizar()`, implementada pelos observadores concretos. A `CentralNotificacoes` mantém uma lista de observadores inscritos, permitindo inscrever (`inscrever`), cancelar inscrições (`cancelar`) e notificar todos (`notificar_todos`). Quando a análise identifica um risco de nível ALTO ou CRÍTICO, a central comunica os observadores registrados.
- **Por que escolhemos:** o Observer permite separar a identificação dos riscos das ações executadas em resposta a eles. Novos observadores podem ser adicionados sem modificar diretamente a lógica de análise climática, reduzindo o acoplamento e facilitando a manutenção e a expansão do sistema.

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

Projeto desenvolvido para a disciplina de Projeto de Software — período 2026.2.

- Gabriel Fernandes Costa Macena
- Gabriel Jatobá
- Gustavo Pereira Cordeiro
