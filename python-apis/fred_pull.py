"""Pull economic series from the FRED API and land them in a CSV."""

import os
import requests
import pandas as pd

# ---------- config ----------
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "GDPC1": "real_gdp",
    "CPIAUCSL": "cpi",
    "UNRATE": "unemployment_rate",
}

START_DATE = "2015-01-01"
END_DATE = "2025-12-31"
PAGE_LIMIT = 100        # small on purpose, to exercise pagination
REQUEST_TIMEOUT = 30
MAX_PAGES = 50
OUTPUT_CSV = "fred_data.csv"


def get_api_key():
    """Read FRED_API_KEY from the environment, or stop with a clear message."""
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise SystemExit(
            "FRED_API_KEY is not set. Get a free key at "
            "https://fredaccount.stlouisfed.org/apikeys and set it with:\n"
            '  [Environment]::SetEnvironmentVariable("FRED_API_KEY", "your_key", "User")'
        )
    return key


def fetch_series(series_id, api_key):
    """Return all observations for one series, handling paging and errors."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": START_DATE,
        "observation_end": END_DATE,
        "limit": PAGE_LIMIT,
        "offset": 0,
    }

    all_observations = []
    page = 0

    while True:
        try:
            response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  [{series_id}] request failed: {type(e).__name__}")
            return []

        data = response.json()
        batch = data["observations"]
        all_observations.extend(batch)
        params["offset"] += len(batch)
        page += 1

        if params["offset"] >= data["count"]:
            break
        if page >= MAX_PAGES:
            print(f"  [{series_id}] hit page cap — returning partial data")
            break

    print(f"  [{series_id}] {len(all_observations)} observations in {page} page(s)")
    return all_observations


def parse_observations(observations, series_id, series_name):
    """Turn raw observation dicts into clean records."""
    records = []
    missing = 0

    for obs in observations:
        raw_value = obs["value"]

        if raw_value == ".":
            missing += 1
            value = None
        else:
            value = float(raw_value)

        records.append({
            "date": obs["date"],
            "series_id": series_id,
            "series_name": series_name,
            "value": value,
        })

    if missing:
        print(f"  [{series_id}] {missing} missing value(s) kept as null")

    return records

def build_dataframe(records):
    """Assemble all records into a single DataFrame."""
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["series_name", "date"]).reset_index(drop=True)
    return df

def main():
    api_key = get_api_key()
    all_records = []

    print(f"Pulling {len(SERIES)} series from FRED ({START_DATE} to {END_DATE})")

    for series_id, series_name in SERIES.items():
        observations = fetch_series(series_id, api_key)

        if not observations:
            print(f"  [{series_id}] SKIPPED — no data returned")
            continue

        records = parse_observations(observations, series_id, series_name)
        all_records.extend(records)

    if not all_records:
        raise SystemExit("No data pulled from any series. Nothing written.")

    df = build_dataframe(all_records)
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\nWrote {len(df)} rows to {OUTPUT_CSV}")
    print(df.groupby("series_name")["value"].agg(["count", "min", "max"]))


if __name__ == "__main__":
    main()