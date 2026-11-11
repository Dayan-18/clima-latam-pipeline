# Clima LATAM · Pipeline de Data Engineering

Pipeline de datos de punta a punta que descarga cada día el clima de **10 capitales latinoamericanas**, lo transforma y valida con **dbt**, y publica un dashboard público en **GitHub Pages**. Todo se ejecuta y despliega automáticamente con **GitHub Actions**. Sin AWS y sin costo.

**Demo:** `https://dayan-18.github.io/clima-latam-pipeline/`
**Documentación dbt (linaje):** `https://dayan-18.github.io/clima-latam-pipeline/docs/`

## Arquitectura

```
 ┌──────────────┐   ┌─────────────┐   ┌──────────────────────────────┐   ┌──────────────────┐
 │ Open-Meteo   │──▶│  Python     │──▶│  DuckDB  (warehouse)         │──▶│  GitHub Pages    │
 │ API (gratis) │   │  extract.py │   │  raw → staging → marts (dbt) │   │  dashboard + docs│
 └──────────────┘   │  load.py    │   │  23 pruebas de calidad       │   │  CSV / Parquet   │
                    └─────────────┘   └──────────────────────────────┘   └──────────────────┘
        ▲                                                                          │
        └──────────── GitHub Actions: cron diario + cada push a main ◀─────────────┘
```

| Capa | Herramienta | Qué hace |
|---|---|---|
| Ingesta | Python + `requests` | Una llamada a la API para las 10 ciudades; guarda el JSON crudo en `data/raw/` |
| Almacenamiento | DuckDB | Base de datos analítica en un solo archivo (`data/warehouse.duckdb`) |
| Transformación | dbt-core + dbt-duckdb | Seeds, staging, marts, pruebas de datos y documentación |
| Orquestación / CI/CD | GitHub Actions | Ejecuta todo a diario (cron) y en cada push; si una prueba falla, no despliega |
| Publicación | GitHub Pages | Dashboard estático, dbt docs y datos abiertos descargables |

## Modelo de datos

```
raw.weather_daily   ─▶ stg_open_meteo__weather_daily ─┬─▶ fct_weather_daily ─┐
seeds.weather_codes ──────────────────────────────────┘                      ├─▶ mart_city_summary
seeds.cities (+ altitud desde staging) ─────────────────▶ dim_cities ────────┘
```

- `fct_weather_daily`: una fila por ciudad y día (observado + pronóstico), con temperatura media, amplitud térmica, descripción del clima y bandera de día lluvioso.
- `dim_cities`: ciudades con altitud y zona horaria.
- `mart_city_summary`: KPIs por ciudad y comparación con el pronóstico de 7 días.

## Calidad de datos

`dbt build` ejecuta 23 pruebas: `unique`, `not_null`, `relationships`, `accepted_values`, una prueba genérica propia (`value_between`) y una prueba singular (`temp_max >= temp_min`). Si alguna falla, el workflow se detiene y la versión anterior del sitio sigue publicada.

## Ejecutarlo en local

Requiere Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m pipeline.run
python -m http.server 8000 --directory public   # abrir http://localhost:8000
```

## Desplegar tu propia copia

1. Haz fork (o sube este código a un repositorio **público** nuevo).
2. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Haz push a `main` (o ve a **Actions → Data pipeline → Run workflow**).
4. En 1–2 minutos el sitio queda en `https://<tu-usuario>.github.io/<repo>/`.

Después se actualiza solo todos los días a las 11:00 UTC.

## Estructura

```
.github/workflows/pipeline.yml   CI/CD: tests → pipeline → deploy a Pages
pipeline/                        extract.py, load.py, export_site.py, run.py
dbt/                             proyecto dbt (seeds, models, tests, macros)
site/index.html                  plantilla del dashboard (Chart.js)
tests/                           pruebas unitarias (pytest)
```

## Fuente de datos

[Open-Meteo](https://open-meteo.com/) — API de clima gratuita y sin API key (licencia CC BY 4.0).
