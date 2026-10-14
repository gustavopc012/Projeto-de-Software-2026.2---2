import requests
from classes import (
    LeituraClima, ResultadoCidade, ProvedorOpenMeteo, ProvedorFicticio, ProvedorCache,
    AlertaAlagamento, AlertaGeada, AlertaCalor, AlertaTempestade, NivelRisco,
    ExportadorConsole, ExportadorCSV, ExportadorJSON
)
from classes import AlertaVento
from cidades import cidades

# * RF6 [A/IF] — Provedores de dados intercambiáveis. 
provedor_base = ProvedorOpenMeteo()
# provedor_base = ProvedorFicticio()  
provedor = ProvedorCache(provedor_base, ttl_segundos=300)

# alertas = [AlertaCalor(), AlertaAlagamento(), AlertaGeada(), AlertaTempestade()]
alertas = [AlertaCalor(), AlertaAlagamento(), AlertaGeada(), AlertaTempestade(), AlertaVento()]

# * RF5 [P] — Avaliação uniforme. O sistema deve avaliar uma coleção mista de alertas e
# * produzir uma avaliação de risco para cada um, sem que a lógica de avaliação saiba qual
# * categoria específica está processando.
def avaliar_alertas_ativos(leitura):
    ativos = []
    for alerta in alertas:
        nivel = alerta.avaliar_risco(leitura)
        if nivel != NivelRisco.NENHUM:
            ativos.append((alerta.mensagem_alerta(leitura), nivel))
    return ativos

def coletar_resultados(provedor, lista_cidades):
    resultados = []
    for cidade in lista_cidades:
        try:
            leitura = provedor.obter_leitura(cidade)
            alertas_ativos = avaliar_alertas_ativos(leitura)
            resultados.append(ResultadoCidade(cidade, leitura, alertas_ativos, ""))
        except ValueError as e:
            resultados.append(ResultadoCidade(cidade, None, [], str(e)))
        except requests.RequestException as e:
            resultados.append(ResultadoCidade(cidade, None, [], f"falha de rede: {e}"))
    return resultados

def demonstrar_rf2():
    leitura_teste = LeituraClima("Maceió", 34.0, 85.0, 10.0)
    print(f"Leitura de teste: {leitura_teste}")
    
    print("'leitura_teste.temperatura = 40.0'...")
    try:
        leitura_teste.temperatura = 40.0
        print("ERRO: O atributo permitiu alteração!")
    except AttributeError as e:
        print(f"Não foi possível alterar os dados: '{e}'.\n")

    print("Nível de risco é calculado no momento da solicitação:")
    alerta_calor = AlertaCalor()
    alerta_alagamento = AlertaAlagamento()
    print(f"Risco de Calor agora: {alerta_calor.avaliar_risco(leitura_teste).value}")
    print(f"Risco de Alagamento agora: {alerta_alagamento.avaliar_risco(leitura_teste).value}\n")
            
def main():
    print("^-^ Sistema de Alertas Meteorológicos Multifonte ^-^")
    while True:
        print("1 - Relatório de uma cidade")
        print("2 - Relatório de todas as cidades")
        print("3 - Exportar relatório consolidado (CSV)")
        print("4 - Exportar relatório consolidado (JSON)")
        print("5 - Buscar cidade personalizada")
        print("6 - Demonstrar RF2")
        print("7 - SAIR")
        escolha = input("Digite o número da opção que deseja: ")

        if escolha == "1":
            for cidade in cidades:
                print(f"-> {cidade}")
            cidade_digitada = input("Digite o nome da cidade que deseja: ")
            if cidade_digitada in cidades:
                res = coletar_resultados(provedor, [cidade_digitada])
                ExportadorConsole().exportar(res)
            else:
                print(f"Erro: A cidade '{cidade_digitada}' não está na lista.")
            # * RF7 [C] — Monitoramento de múltiplas localidades. O sistema deve monitorar várias
            # * localidades e produzir um único relatório consolidado.
        elif escolha == "2":
            res = coletar_resultados(provedor, cidades)
            ExportadorConsole().exportar(res)

        elif escolha == "3":
            res = coletar_resultados(provedor, cidades)
            ExportadorCSV().exportar(res, "relatorio.csv")
            print("\nRelatório CSV gerado com sucesso!\n")

        elif escolha == "4":
            res = coletar_resultados(provedor, cidades)
            ExportadorJSON().exportar(res, "relatorio.json")
            print("\nRelatório JSON gerado com sucesso!\n")

        elif escolha == "5":
            cidade_digitada = input("Digite o nome da cidade que deseja: ")
            res = coletar_resultados(provedor, [cidade_digitada])
            ExportadorConsole().exportar(res)
        elif escolha == "6":
            demonstrar_rf2()
        elif escolha == "7":
            break    
        else:
            print("Escolha um número existente.")
            
main()
