import requests

def obter_localizacao_cidade(cidade: str) -> tuple[float, float]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": cidade,
        "count": 1,
        "language": "pt",
        "format": "json"
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError:
        raise ValueError("Respota de geodecodificação não é JSON válido")

    resultados = data.get("results", [])
    if not resultados:
        raise ValueError(f"Localidade desconhecida: {cidade}")

    r = resultados[0]
    return r["latitude"], r["longitude"]

# ! ------------

def buscar_previsao(latitude: float, longitude: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,rain",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        raise ValueError("Resposta da previsão não é JSON válido")    

