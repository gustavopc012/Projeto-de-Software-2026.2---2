import requests


# ==========================================================================
# PADRÃO ESTRUTURAL: FACADE
# Esconde o fluxo de duas chamadas HTTP (geocodificação + previsão) atrás de
# um único método simples: obter_clima_completo(cidade).
# ==========================================================================
class OpenMeteoFacade:
    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    CAMPOS_ATUAIS = "temperature_2m,relative_humidity_2m,rain,wind_speed_10m"

    def __init__(self, timeout: float = 10):
        self._timeout = timeout

    def obter_clima_completo(self, cidade: str) -> dict:
        """Faz a geocodificação e busca a previsão atual da cidade.

        Retorna sempre um dicionário no formato:
            {"localidade": {"nome", "estado", "pais"}, "current": {...}}

        Lança:
            ValueError  -> localidade inexistente ou JSON malformado (RF8)
            requests.RequestException -> falha de rede/HTTP (RF8)
        """
        # Passo 1: descobrir latitude e longitude
        dados_geo = self._get_json(
            self.GEO_URL,
            {"name": cidade, "count": 1, "language": "pt", "format": "json"},
            "geocodificação",
        )
        resultados = dados_geo.get("results") or []
        if not isinstance(resultados, list) or not resultados:
            # [RF8] Localidade inexistente: erro tratado, sem travar o sistema.
            raise ValueError(f"Localidade desconhecida: '{cidade}'")

        local = resultados[0]
        if not isinstance(local, dict):
            raise ValueError("Resposta de geocodificação em formato inesperado")
        lat, lon = local.get("latitude"), local.get("longitude")
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            raise ValueError("Geocodificação não retornou coordenadas válidas")

        # Passo 2: buscar o clima atual nas coordenadas encontradas
        dados_clima = self._get_json(
            self.WEATHER_URL,
            {"latitude": lat, "longitude": lon, "current": self.CAMPOS_ATUAIS},
            "previsão",
        )
        atual = dados_clima.get("current")
        if not isinstance(atual, dict):
            raise ValueError("Resposta da previsão não contém o bloco 'current'")

        return {
            "localidade": {
                "nome": local.get("name") or cidade,
                "estado": local.get("admin1") or "",
                "pais": local.get("country") or "",
            },
            "current": atual,
        }

    def _get_json(self, url: str, params: dict, contexto: str) -> dict:
        """Faz o GET e garante que o corpo seja um objeto JSON (dict)."""
        resposta = requests.get(url, params=params, timeout=self._timeout)

        # A Open-Meteo devolve {"error": true, "reason": "..."} em erros 4xx
        if resposta.status_code >= 400:
            motivo = ""
            try:
                corpo = resposta.json()
                if isinstance(corpo, dict):
                    motivo = corpo.get("reason", "")
            except ValueError:
                pass
            if motivo:
                raise ValueError(f"API recusou a requisição de {contexto}: {motivo}")
            resposta.raise_for_status()

        try:
            corpo = resposta.json()
        except ValueError:
            # [RF8] Dados malformados viram ValueError tratável.
            raise ValueError(f"Resposta de {contexto} não é um JSON válido")

        if not isinstance(corpo, dict):
            raise ValueError(f"Resposta de {contexto} em formato inesperado")
        return corpo
