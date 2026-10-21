# Sistema de Alertas Meteorológicos Multifonte
Este projeto é um sistema em Python orientado a objetos desenvolvido para monitorar condições climáticas de múltiplas localidades em tempo real, avaliar níveis de risco meteorológico e gerar relatórios consolidados em diferentes formatos.

## Funcionalidades
- **RF1 [E] — Dados climáticos protegidos**. Os dados climáticos obtidos da API jamais podem
existir em estado inválido ou inconsistente.
- **RF2 [E] — Calculado, não atribuível**. Código externo não pode alterar uma leitura climática
após a obtenção; valores derivados devem ser calculados.
- **RF3 [A/H] — Múltiplas categorias de alerta.** O sistema deve suportar pelo menos quatro
categorias distintas de alerta meteorológico, cada uma avaliando o perigo com critérios próprios
aplicados aos mesmos dados climáticos.
- **RF4 [P] — Alertas autodescritivos.** Cada categoria de alerta deve se descrever de forma
legível e apropriada ao seu tipo quando exibida em uma lista genérica.
- **RF5 [P] — Avaliação uniforme.** O sistema deve avaliar uma coleção mista de alertas e
produzir uma avaliação de risco para cada um, sem que a lógica de avaliação saiba qual
categoria específica está processando.
- **RF6 [A/IF] — Provedores de dados intercambiáveis**. O sistema deve poder trocar de
provedor de dados climáticos sem alterações na lógica de avaliação de alertas.
- **RF7 [C] — Monitoramento de múltiplas localidades.** O sistema deve monitorar várias
localidades e produzir um único relatório consolidado.
- **RF8 [X] — Falha graciosa.** O sistema não pode travar quando a API estiver inacessível,
retornar dados malformados ou for consultada sobre uma localidade inexistente.
- **RF9 [A] — Múltiplos formatos de relatório.** O sistema deve exportar relatórios em pelo
menos dois formatos, com a escolha do formato desacoplada da geração do relatório.
- **RF10 [E] — Cache transparente.** Requisições repetidas para a mesma localidade em um
curto intervalo não devem sempre gerar nova chamada de rede, e isso deve ser invisível para o
código solicitante.

## Como Executar

1. Certifique-se de ter o Python 3.10+ e a biblioteca `requests` instalados:
   ```bash
   pip install requests

-------------------------------------------------------------------------------------------------------------------------

## Padrões de Projeto Criacionais Aplicados (Etapa 2)

Nesta etapa, refatoramos o projeto aplicando dois padrões criacionais do catálogo GoF:

### 1. Builder (`ResultadoCidade.Builder`)

* **Onde foi aplicado:** Na construção dos objetos imutáveis `ResultadoCidade` (em `classes.py` e utilizado em `coletar_resultados()` no `main.py`).
* **Problema identificado no código original:** A classe `ResultadoCidade` representava dois cenários distintos (sucesso na leitura climática com alertas ativos ou falha graciosa de rede/validação do RF8) através de um único construtor posicional. Isso obrigava o código cliente a passar argumentos vazios ou nulos sem semântica clara (`ResultadoCidade(cidade, leitura, alertas_ativos, "")` ou `ResultadoCidade(cidade, None, [], str(e))`).
* **Justificativa e Solução:** Implementamos um `Builder` interno com interface fluente (`.com_leitura()`, `.com_alertas()`, `.com_erro()`, `.build()`). Isso eliminou os parâmetros posicionais nulos/vazios, manteve a imutabilidade de `ResultadoCidade` após sua criação e centralizou a validação de consistência no método `build()` (garantindo que um resultado nunca exista sem leitura e sem erro ao mesmo tempo).

### 2. Factory Method (`GeradorRelatorioCreator`)

* **Onde foi aplicado:** Na hierarquia de geração e exportação de relatórios do RF9 (`GeradorRelatorioCreator` e suas subclasses `GeradorConsoleCreator`, `GeradorCSVCreator` e `GeradorJSONCreator` em `classes.py`).
* **Problema identificado no código original:** O código cliente (`main.py`) estava diretamente acoplado às classes concretas de exportação (`ExportadorConsole`, `ExportadorCSV`, `ExportadorJSON`), instanciando-as manualmente dentro de blocos condicionais (`if/elif`) no loop principal.
* **Justificativa e Solução:** Criamos a classe abstrata `GeradorRelatorioCreator` contendo o **Factory Method** `criar_exportador()` e o método de operação `gerar_relatorio()`. Cada formato ganhou seu próprio `ConcreteCreator`. Assim, o `main.py` deixou de conhecer e importar as classes concretas dos exportadores, permitindo adicionar novos formatos de exportação no futuro (ex.: PDF ou HTML) apenas criando uma nova subclasse de `Creator`, sem modificar a lógica de execução do relatório.

--------------------------------------------------------------------------------------------------------------------------

## Padrões de Projeto Estruturais Aplicados (Etapa 3)

Após a aula sobre Padrões Estruturais, identificamos pontos no sistema onde a composição de classes poderia reduzir o acoplamento com a rede e melhorar a flexibilidade, aplicando **três** padrões estruturais do catálogo GoF:

### 1. Facade (`OpenMeteoFacade` em `api.py`)
* **Problema atacado:** O fluxo para consultar o clima na API do Open-Meteo era complexo e fragmentado. Primeiro, exigia-se uma chamada HTTP de geocodificação para transformar o nome da cidade em Latitude/Longitude. Com as coordenadas em mãos, era necessária uma segunda chamada HTTP para obter o clima em si. Isso gerava um conhecimento excessivo sobre o funcionamento do subsistema espalhado no código.
* **Método usado:** Criamos a classe `OpenMeteoFacade` com um único método `obter_clima_completo(cidade)`, que orquestra as duas requisições internamente.
* **Porquê escolhemos:** O Facade forneceu uma "porta de entrada simples para um subsistema complicado". Ele isola toda a complexidade de rotas, navegação em URLs e tratamento de JSON, oferecendo ao restante da aplicação uma interface clara e de alto nível.

### 2. Adapter (`ProvedorOpenMeteo` em `classes.py`)
* **Problema atacado:** O núcleo do nosso sistema de Alertas foi desenhado para avaliar objetos de domínio altamente validados (`LeituraClima`). Contudo, o Facade da API externa retorna um Dicionário cru (JSON) com chaves muito específicas (`temperature_2m`, `relative_humidity_2m`).
* **Método usado:** O `ProvedorOpenMeteo` foi construído como um **Adapter** de Objeto. Ele assina o contrato esperado pelo sistema (a interface `ProvedorClima`), abraça o Facade (o *Adaptee*) e traduz o JSON em instâncias de `LeituraClima`.
* **Porquê escolhemos:** O Adapter resolve a incompatibilidade estrutural. Ele atua como uma fronteira: o nosso sistema não sabe o que é JSON e a API não sabe o que é `LeituraClima`. O acoplamento com o provedor fica inteiramente contido nessa classe.

### 3. Proxy (`ProvedorCache` em `classes.py` resolvendo o RF10)
* **Problema atacado:** Consultar APIs externas gasta banda, atrasa a execução e frequentemente esbarra em *rate limits* (bloqueios por excesso de chamadas). Precisávamos mitigar isso sem poluir a rotina principal (que apenas solicita os dados).
* **Método usado:** Formalizamos a classe `ProvedorCache` como um **Virtual/Caching Proxy**. Ela herda da mesma abstração `ProvedorClima` do provedor real, mas seu comportamento intercepta o método `obter_leitura`.
* **Porquê escolhemos:** Segundo a definição GoF, o Proxy "controla o acesso ao objeto real". Quando o `main.py` pede o clima de uma cidade, o Proxy avalia se já tem o dado em memória dentro do seu tempo de vida (TTL). Se tiver, ele "mente" para o cliente e devolve a resposta instantaneamente sem bater na rede; caso contrário, delega ao provedor real de forma completamente invisível, cumprindo perfeitamente a exigência técnica do Requisito Funcional 10.