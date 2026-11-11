"""Pipeline entrypoint: python -m pipeline.run

  1. Extract  -> Open-Meteo API to data/raw/*.json
  2. Load     -> raw JSON to DuckDB (raw.weather_daily)
  3. Transform-> dbt build (seeds + models + data tests) and dbt docs
  4. Publish  -> static dashboard + data files in public/ (deployed to GitHub Pages)
"""
import os
import shutil
import sys
import time

from dbt.cli.main import dbtRunner

from pipeline.config import DBT_DIR, DUCKDB_PATH
from pipeline.export_site import export_site
from pipeline.extract import extract
from pipeline.load import load


def run_dbt(*args: str) -> None:
    result = dbtRunner().invoke(
        [*args, "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)]
    )
    if not result.success:
        sys.exit(f"dbt {' '.join(args)} failed")


def main() -> None:
    # Forward slashes so the path is safe inside profiles.yml on Windows too
    os.environ["DUCKDB_PATH"] = DUCKDB_PATH.as_posix()
    start = time.perf_counter()

    print("[1/4] Extract: Open-Meteo API")
    raw_path = extract()

    print("[2/4] Load: DuckDB raw layer")
    load(raw_path)

    print("[3/4] Transform + test: dbt build")
    run_dbt("build")
    # `docs generate` overwrites run_results.json, so keep the build results
    target = DBT_DIR / "target"
    shutil.copy(target / "run_results.json", target / "build_results.json")
    run_dbt("docs", "generate", "--static")

    print("[4/4] Publish: static site")
    export_site()

    print(f"Pipeline finished in {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
