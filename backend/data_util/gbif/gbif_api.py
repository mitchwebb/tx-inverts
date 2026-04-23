import requests


async def gbif_keyed_api_request(endpoint: str, key: str):
    response = requests.get(f"https://api.gbif.org/v1/{endpoint}/{key}")
    data = response.json()

    return data
