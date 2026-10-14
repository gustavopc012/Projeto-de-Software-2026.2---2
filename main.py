import requests
from classes import (
    LeituraClima, ResultadoCidade, ProvedorOpenMeteo, ProvedorFicticio, ProvedorCache,
    AlertaAlagamento, AlertaGeada, AlertaCalor, AlertaTempestade, AlertaVento, NivelRisco,
    GeradorRelatorioCreator, GeradorConsoleCreator, GeradorCSVCreator, GeradorJSONCreator
)
from cidades import cidades

# RF6 [A/IF] — Provedores de dados intercambiáveis.
provedor_base = ProvedorOpenMeteo()
# provedor_base = ProvedorFicticio()
provedor = ProvedorCache(provedor_base, ttl_segundos=300)

alertas = [AlertaCalor(), AlertaAlagamento(), AlertaGeada(), AlertaTempestade(), AlertaVento()]

# RF5 [P] — Avaliação uniforme.
def avaliar_alertas_ativos(leitura):
    ativos = []
    for alerta in alertas:
        nivel = alerta.avaliar_risco(leitura)
        if nivel != NivelRisco.NENHUM:
            ativos.append((alerta.mensagem_alerta(leitura), nivel))
    return ativos

# Uso do padrão BUILDER para montar ResultadoCidade passo a passo
def coletar_resultados(provedor, lista_cidades):
    resultados = []
    for cidade in lista_cidades:
        builder = ResultadoCidade.Builder(cidade)
        try:
            leitura = provedor.obter_leitura(cidade)
            alertas_ativos = avaliar_alertas_ativos(leitura)
            resultado = (
                builder
                .com_leitura(leitura)
                .com_alertas(alertas_ativos)
                .build()
            )
        except ValueError as e:
            resultado = builder.com_erro(str(e)).build()
        except requests.RequestException as e:
            resultado = builder.com_erro(f"falha de rede: {e}").build()
        
        resultados.append(resultado)
    return resultados

# Cliente do FACTORY METHOD: trabalha apenas com a abstração GeradorRelatorioCreator
def executar_relatorio(criador: GeradorRelatorioCreator, lista_cidades: list[str]):
    resultados = coletar_resultados(provedor, lista_cidades)
    criador.gerar_relatorio(resultados)

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
    # Mapa de Creators (Factory Method) para relatórios consolidados
    criadores_consolidados = {
        "2": GeradorConsoleCreator(),
        "3": GeradorCSVCreator("relatorio.csv"),
        "4": GeradorJSONCreator("relatorio.json"),
    }
    criador_console = GeradorConsoleCreator()

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
                executar_relatorio(criador_console, [cidade_digitada])
            else:
                print(f"Erro: A cidade '{cidade_digitada}' não está na lista.")

        elif escolha in criadores_consolidados:
            executar_relatorio(criadores_consolidados[escolha], cidades)

        elif escolha == "5":
            cidade_digitada = input("Digite o nome da cidade que deseja: ")
            executar_relatorio(criador_console, [cidade_digitada])

        elif escolha == "6":
            demonstrar_rf2()

        elif escolha == "7":
            break    
        else:
            print("Escolha um número existente.")
            
if __name__ == "__main__":
    main()
