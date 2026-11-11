"""LOAD: flatten the raw JSON into rows and load them into DuckDB (schema `raw`).
No business logic here: transformations belong to dbt."""
import json
import sys
from pathlib import Path

import duckdb

from pipeline.config import DAILY_VARS, DUCKDB_PATH, RAW_DIR

COLUMNS = [
    "city_id", "weather_date", *DAILY_VARS,
    "latitude", "longitude", "elevation", "timezone", "extracted_at",
]


def flatten(document: dict) -> list[tuple]:
    """Turn {city -> daily arrays} into one row per city per day."""
    rows = []
    for city_id, resp in zip(document["city_ids"], document["responses"]):
        daily = resp["daily"]
        for i, day in enumerate(daily["time"]):
            rows.append((
                city_id,
                day,
                *(daily[var][i] for var in DAILY_VARS),
                resp["latitude"],
                resp["longitude"],
                resp.get("elevation"),
                resp.get("timezone"),
                document["extracted_at"],
            ))
    return rows


def load(raw_path: Path, db_path: Path = DUCKDB_PATH) -> int:
    document = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    rows = flatten(document)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as con:
        con.execute("create schema if not exists raw")
        # Each extraction brings the full window (past + forecast), so a full
        # refresh keeps the load idempotent: re-running never duplicates data.
        con.execute("""
            create or replace table raw.weather_daily (
                city_id varchar,
                weather_date date,
                temperature_2m_max double,
                temperature_2m_min double,
                precipitation_sum double,
                wind_speed_10m_max double,
                weather_code integer,
                latitude double,
                longitude double,
                elevation double,
                timezone varchar,
                extracted_at timestamptz
            )
        """)
        placeholders = ", ".join("?" for _ in COLUMNS)
        con.executemany(f"insert into raw.weather_daily values ({placeholders})", rows)
    print(f"  {len(rows)} rows loaded into raw.weather_daily")
    return len(rows)


if __name__ == "__main__":
    latest = Path(sys.argv[1]) if len(sys.argv) > 1 else max(RAW_DIR.glob("*.json"))
    load(latest)
