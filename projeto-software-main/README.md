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