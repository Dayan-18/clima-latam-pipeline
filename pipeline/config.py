"""Central configuration: paths and API parameters."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"                     # landing zone (raw JSON as received)
DUCKDB_PATH = DATA_DIR / "warehouse.duckdb"    # analytical warehouse

DBT_DIR = ROOT / "dbt"
CITIES_SEED = DBT_DIR / "seeds" / "cities.csv"  # single source of truth for cities

SITE_SRC = ROOT / "site"     # dashboard template
PUBLIC_DIR = ROOT / "public"  # what gets deployed to GitHub Pages

API_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
    "weather_code",
]
PAST_DAYS = 60       # observed history
FORECAST_DAYS = 7    # forecast horizon
