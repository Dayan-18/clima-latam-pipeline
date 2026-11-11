"""PUBLISH: read the dbt marts and build the static site in public/:
  public/index.html                 dashboard
  public/data.json                  data consumed by the dashboard
  public/data/*.csv, *.parquet      open data downloads
  public/docs/index.html            dbt documentation + lineage graph
"""
import json
import os
import shutil
from datetime import datetime, timezone

import duckdb

from pipeline.config import DBT_DIR, DUCKDB_PATH, PUBLIC_DIR, SITE_SRC


def _rows(con, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _dbt_test_stats() -> dict:
    """Count data tests from the `dbt build` results (shown on the dashboard)."""
    path = DBT_DIR / "target" / "build_results.json"
    if not path.exists():
        return {"passed": 0, "total": 0}
    results = json.loads(path.read_text(encoding="utf-8")).get("results", [])
    tests = [r for r in results if r["unique_id"].startswith("test.")]
    return {"passed": sum(r["status"] == "pass" for r in tests), "total": len(tests)}


def export_site() -> None:
    if PUBLIC_DIR.exists():
        shutil.rmtree(PUBLIC_DIR)
    shutil.copytree(SITE_SRC, PUBLIC_DIR)
    (PUBLIC_DIR / "data").mkdir()

    # Same config as dbt's in-process connection (DuckDB rejects mixed configs)
    with duckdb.connect(str(DUCKDB_PATH)) as con:
        summary = _rows(con, "select * from marts.mart_city_summary order by city_name")
        daily = _rows(con, """
            select city_id, weather_date, temp_max_c, temp_min_c, precipitation_mm,
                   weather_description, weather_category, is_forecast
            from marts.fct_weather_daily
            order by city_id, weather_date
        """)
        for table in ("fct_weather_daily", "dim_cities", "mart_city_summary"):
            for fmt in ("csv", "parquet"):
                target = (PUBLIC_DIR / "data" / f"{table}.{fmt}").as_posix()
                con.execute(f"copy marts.{table} to '{target}' (format {fmt})")

    by_city: dict[str, list] = {}
    for row in daily:
        by_city.setdefault(row.pop("city_id"), []).append(row)

    repo = os.environ.get("GITHUB_REPOSITORY")  # set automatically by GitHub Actions
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Open-Meteo (open-meteo.com)",
        "repo_url": f"https://github.com/{repo}" if repo else None,
        "dbt_tests": _dbt_test_stats(),
        "row_count": len(daily),
        "cities": summary,
        "daily": by_city,
    }
    (PUBLIC_DIR / "data.json").write_text(
        json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8"
    )

    docs = DBT_DIR / "target" / "static_index.html"
    if docs.exists():
        (PUBLIC_DIR / "docs").mkdir()
        shutil.copy(docs, PUBLIC_DIR / "docs" / "index.html")

    print(f"  Site ready in {PUBLIC_DIR.name}/ ({len(summary)} cities, {len(daily)} rows)")


if __name__ == "__main__":
    export_site()
