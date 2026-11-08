import sys

import requests

from cidades import cidades
from classes import (
    Alerta, AlertaAlagamento, AlertaAtivo, AlertaCalor, AlertaGeada, AlertaTempestade, AlertaVento,
    GeradorConsoleCreator, GeradorCSVCreator, GeradorJSONCreator, GeradorRelatorioCreator,
    LeituraClima, NivelRisco, ProvedorCache, ProvedorClima, ProvedorFicticio, ProvedorOpenMeteo,
    ResultadoCidade, LINHA_DUPLA, LINHA_SIMPLES,
)

# Garante que emojis e acentos saiam corretamente mesmo em terminais
# Windows com outra codificação ou quando a saída é redirecionada.
for _fluxo in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# [RF6] Provedores intercambiáveis: para trocar a fonte de dados basta
# trocar a linha abaixo. Nada na avaliação de alertas precisa mudar.
provedor_base: ProvedorClima = ProvedorOpenMeteo()
# provedor_base = ProvedorFicticio()   # modo offline com dados fixos

# [RF10] Cache transparente: o Proxy envolve o provedor real (TTL de 5 min).
provedor: ProvedorClima = ProvedorCache(provedor_base, ttl_segundos=300)

# [RF3] Coleção mista com as cinco categorias de alerta.
alertas: list[Alerta] = [AlertaCalor(), AlertaAlagamento(), AlertaGeada(), AlertaTempestade(), AlertaVento()]


def avaliar_alertas_ativos(leitura: LeituraClima) -> list[AlertaAtivo]:
    # [RF5] Avaliação uniforme: o mesmo laço trata todos os alertas pela
    # interface Alerta (polimorfismo), sem saber qual categoria concreta está
    # sendo processada. Não há if/isinstance por tipo.
    ativos = []
    for alerta in alertas:
        nivel = alerta.avaliar_risco(leitura)
        if nivel != NivelRisco.NENHUM:
            ativos.append(AlertaAtivo(alerta.nome, alerta.icone, nivel, alerta.mensagem_alerta(leitura)))
    return ativos


def coletar_resultados(provedor: ProvedorClima, lista_cidades: list[str]) -> list[ResultadoCidade]:
    # [RF7] Monitoramento de múltiplas localidades: percorre todas as cidades
    # e junta os resultados em uma única lista, usada no relatório consolidado.
    resultados = []
    for cidade in lista_cidades:
        builder = ResultadoCidade.Builder(cidade)  # PADRÃO BUILDER
        try:
            leitura = provedor.obter_leitura(cidade)
            resultado = builder.com_leitura(leitura).com_alertas(avaliar_alertas_ativos(leitura)).build()
        # [RF8] Falha graciosa: cada falha vira um ResultadoCidade com erro e
        # o laço segue para a próxima cidade. O sistema nunca trava.
        except requests.Timeout:
            resultado = builder.com_erro("tempo de resposta da API esgotado").build()
        except requests.ConnectionError:
            resultado = builder.com_erro("API inacessível (verifique sua conexão)").build()
        except requests.RequestException as e:
            resultado = builder.com_erro(f"falha de rede: {e}").build()
        except ValueError as e:  # localidade inexistente, JSON malformado, dado inválido (RF1)
            resultado = builder.com_erro(str(e)).build()
        except Exception as e:  # rede de segurança para qualquer imprevisto
            resultado = builder.com_erro(f"erro inesperado: {type(e).__name__}: {e}").build()
        resultados.append(resultado)
    return resultados


def executar_relatorio(criador: GeradorRelatorioCreator, lista_cidades: list[str]) -> None:
    # Cliente do FACTORY METHOD: conhece apenas a abstração do Creator.
    resultados = coletar_resultados(provedor, lista_cidades)
    try:
        criador.gerar_relatorio(resultados)
    except OSError as e:  # [RF8] ex.: arquivo aberto no Excel, sem permissão
        print(f"\n❌ Não foi possível salvar o relatório: {e}")


def demonstrar_rf2() -> None:
    print(f"\n{LINHA_SIMPLES}\n  🔒 Demonstração do RF1, RF2 e RF4\n{LINHA_SIMPLES}")
    leitura = LeituraClima("Maceió", 34.0, 85.0, 10.0, 20.0)
    print(f"Leitura de teste: {leitura}")

    print("\n▶ Tentando executar 'leitura.temperatura = 40.0'...")
    try:
        leitura.temperatura = 40.0
        print("   ❌ ERRO: o atributo permitiu alteração!")
    except AttributeError as e:
        print(f"   ✅ Alteração bloqueada: {e}")

    print("\n▶ Valores derivados são calculados no momento da leitura:")
    print(f"   Sensação térmica: {leitura.sensacao_termica}°C")
    for alerta in (AlertaCalor(), AlertaAlagamento()):
        print(f"   Risco de {alerta.nome}: {alerta.avaliar_risco(leitura)}")

    print("\n▶ Tentando criar uma leitura inválida (umidade = 150%)...")
    try:
        LeituraClima("Maceió", 30.0, 150.0, 0.0)
        print("   ❌ ERRO: a leitura inválida foi aceita!")
    except ValueError as e:
        print(f"   ✅ Leitura rejeitada: {e}")

    print("\n▶ Alertas se descrevendo em uma lista genérica:")
    for alerta in alertas:
        print(f"   • {alerta}")


def ler_entrada(mensagem: str) -> str | None:
    try:
        return input(mensagem).strip()
    except (EOFError, KeyboardInterrupt):
        return None


def localizar_cidade(texto: str) -> str | None:
    """Busca na lista ignorando maiúsculas/minúsculas, ou pelo número."""
    if texto.isdigit() and 1 <= int(texto) <= len(cidades):
        return cidades[int(texto) - 1]
    return next((c for c in cidades if c.casefold() == texto.casefold()), None)


def exibir_menu() -> None:
    print(f"\n{LINHA_DUPLA}")
    print("  🌦️  SISTEMA DE ALERTAS METEOROLÓGICOS MULTIFONTE")
    print(LINHA_DUPLA)
    print("  1 · 📍 Relatório de uma cidade")
    print("  2 · 🗺️  Relatório de todas as cidades")
    print("  3 · 📄 Exportar relatório consolidado (CSV)")
    print("  4 · 🧾 Exportar relatório consolidado (JSON)")
    print("  5 · 🔎 Buscar cidade personalizada")
    print("  6 · 🔒 Demonstrar proteção dos dados (RF1/RF2/RF4)")
    print("  7 · 🚪 Sair")
    print(LINHA_SIMPLES)


def main() -> None:
    # Mapa de Creators (Factory Method) para os relatórios consolidados
    criadores_consolidados = {
        "2": GeradorConsoleCreator(),
        "3": GeradorCSVCreator("relatorio.csv"),
        "4": GeradorJSONCreator("relatorio.json"),
    }
    criador_individual = GeradorConsoleCreator(com_resumo=False)

    while True:
        exibir_menu()
        escolha = ler_entrada("👉 Digite o número da opção: ")
        if escolha is None or escolha == "7":
            print("\n👋 Até logo!")
            break

        if escolha == "1":
            for i, cidade in enumerate(cidades, start=1):
                print(f"   {i}. {cidade}")
            texto = ler_entrada("👉 Digite o nome ou número da cidade: ") or ""
            cidade = localizar_cidade(texto)
            if cidade:
                executar_relatorio(criador_individual, [cidade])
            else:
                print(f"\n⚠️  A cidade '{texto}' não está na lista. Use a opção 5 para outras cidades.")

        elif escolha in criadores_consolidados:
            print("\n⏳ Consultando as cidades monitoradas...")
            executar_relatorio(criadores_consolidados[escolha], cidades)

        elif escolha == "5":
            texto = ler_entrada("👉 Digite o nome da cidade: ")
            if texto:
                executar_relatorio(criador_individual, [texto])
            else:
                print("\n⚠️  O nome da cidade não pode ficar vazio.")

        elif escolha == "6":
            demonstrar_rf2()

        else:
            print("\n⚠️  Opção inválida. Escolha um número de 1 a 7.")


if __name__ == "__main__":
    main()
