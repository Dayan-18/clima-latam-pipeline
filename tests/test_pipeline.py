"""Unit tests for the Python part of the pipeline (no network needed)."""
import json

import duckdb

from pipeline.extract import load_cities
from pipeline.load import flatten, load


def fake_document():
    return {
        "extracted_at": "2026-11-10T12:00:00+00:00",
        "city_ids": ["lima", "quito"],
        "responses": [
            {
                "latitude": -12.05, "longitude": -77.06, "elevation": 148.0,
                "timezone": "America/Lima",
                "daily": {
                    "time": ["2026-11-09", "2026-11-10"],
                    "temperature_2m_max": [26.0, 25.7],
                    "temperature_2m_min": [22.8, 22.6],
                    "precipitation_sum": [0.7, None],
                    "wind_speed_10m_max": [17.7, 18.9],
                    "weather_code": [3, 51],
                },
            },
            {
                "latitude": -0.18, "longitude": -78.47, "elevation": 2850.0,
                "timezone": "America/Guayaquil",
                "daily": {
                    "time": ["2026-11-09", "2026-11-10"],
                    "temperature_2m_max": [19.1, 18.4],
                    "temperature_2m_min": [9.2, 9.9],
                    "precipitation_sum": [4.2, 1.1],
                    "wind_speed_10m_max": [10.0, 11.5],
                    "weather_code": [61, 80],
                },
            },
        ],
    }


def test_cities_seed_is_valid():
    cities = load_cities()
    ids = [c["city_id"] for c in cities]
    assert len(cities) == 10
    assert len(ids) == len(set(ids)), "city_id must be unique"
    for c in cities:
        assert -90 <= float(c["latitude"]) <= 90
        assert -180 <= float(c["longitude"]) <= 180


def test_flatten_one_row_per_city_per_day():
    rows = flatten(fake_document())
    assert len(rows) == 4
    assert rows[0][0] == "lima" and rows[0][1] == "2026-11-09"
    assert rows[3][0] == "quito" and rows[3][1] == "2026-11-10"


def test_load_is_idempotent(tmp_path):
    raw = tmp_path / "raw.json"
    raw.write_text(json.dumps(fake_document()), encoding="utf-8")
    db = tmp_path / "test.duckdb"

    load(raw, db)
    load(raw, db)  # running twice must not duplicate rows

    with duckdb.connect(str(db)) as con:
        assert con.execute("select count(*) from raw.weather_daily").fetchone()[0] == 4
