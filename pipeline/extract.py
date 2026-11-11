"""EXTRACT: download daily weather for every city from the Open-Meteo API
and store the response untouched in the landing zone (data/raw)."""
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from pipeline.config import (
    API_URL, CITIES_SEED, DAILY_VARS, FORECAST_DAYS, PAST_DAYS, RAW_DIR,
)


def load_cities(path: Path = CITIES_SEED) -> list[dict]:
    """Read the cities seed (the same CSV that dbt loads as a table)."""
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fetch_weather(cities: list[dict], retries: int = 3) -> list[dict]:
    """One API call for all cities (Open-Meteo accepts comma-separated coordinates)."""
    params = {
        "latitude": ",".join(c["latitude"] for c in cities),
        "longitude": ",".join(c["longitude"] for c in cities),
        "daily": ",".join(DAILY_VARS),
        "past_days": PAST_DAYS,
        "forecast_days": FORECAST_DAYS,
        "timezone": "auto",
    }
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(API_URL, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            # With a single coordinate the API returns an object, not a list
            return payload if isinstance(payload, list) else [payload]
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"  API error ({exc}); retrying in {wait}s...")
            time.sleep(wait)
    return []


def save_raw(responses: list[dict], cities: list[dict], extracted_at: datetime) -> Path:
    """Persist the raw payload with metadata (lineage: who, when, from where)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"open_meteo_{extracted_at:%Y%m%dT%H%M%SZ}.json"
    document = {
        "source": API_URL,
        "extracted_at": extracted_at.isoformat(),
        "city_ids": [c["city_id"] for c in cities],
        "responses": responses,
    }
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def extract() -> Path:
    cities = load_cities()
    extracted_at = datetime.now(timezone.utc).replace(microsecond=0)
    responses = fetch_weather(cities)
    if len(responses) != len(cities):
        raise ValueError(f"Expected {len(cities)} responses, got {len(responses)}")
    path = save_raw(responses, cities, extracted_at)
    print(f"  {len(cities)} cities downloaded -> {path.relative_to(RAW_DIR.parent.parent)}")
    return path


if __name__ == "__main__":
    extract()
