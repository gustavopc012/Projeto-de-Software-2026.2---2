import requests

# * PADRÃO ESTRUTURAL: FACADE
# Esconde o fluxo complexo de múltiplas chamadas à API em uma interface simples.
class OpenMeteoFacade:
    def __init__(self):
        self._geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        self._weather_url = "https://api.open-meteo.com/v1/forecast"

    def obter_clima_completo(self, cidade: str) -> dict:
        """Porta de entrada unificada: faz a geocodificação e já busca a previsão."""
        # Passo 1: Descobrir Lat e Lon
        params_geo = {"name": cidade, "count": 1, "language": "pt", "format": "json"}
        resp_geo = requests.get(self._geo_url, params=params_geo, timeout=10)
        resp_geo.raise_for_status()
        
        try:
            resultados = resp_geo.json().get("results", [])
        except ValueError:
            raise ValueError("Resposta de geodecodificação não é um JSON válido")

        if not resultados:
            raise ValueError(f"Localidade desconhecida: {cidade}")

        lat, lon = resultados[0]["latitude"], resultados[0]["longitude"]

        # Passo 2: Buscar a previsão com a Lat e Lon
        params_weather = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,rain",
        }
        resp_weather = requests.get(self._weather_url, params=params_weather, timeout=10)
        resp_weather.raise_for_status()

        try:
            return resp_weather.json()
        except ValueError:
            raise ValueError("Resposta da previsão não é um JSON válido")