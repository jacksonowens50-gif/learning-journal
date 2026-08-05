
import os
import requests

api_key = os.getenv("FRED_API_KEY")

url = "https://api.stlouisfed.org/fred/series/observations"

params = {
    "series_id": "UNRATE",
    "api_key": api_key,
    "file_type": "json",
    "observation_start": "2015-01-01",
    "observation_end": "2025-12-31",
    "limit": 100,
    "offset": 100
}

try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    raise SystemExit(f"Request failed: {e}")

all_observations = []
offset = 0
page = 0

while True:
    params["offset"] = offset
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    batch = data["observations"]
    all_observations.extend(batch)
    offset += len(batch)
    page += 1

    print(f"page {page}: got {len(batch)}, total {offset} of {data['count']}")

    if offset >= data["count"]:
        break
    if page >= 50:
        raise SystemExit("Too many pages — something is wrong")