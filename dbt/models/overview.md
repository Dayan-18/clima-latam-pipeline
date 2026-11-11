{% docs __overview__ %}
# Clima LATAM · Data pipeline

Daily weather for 10 Latin American capitals, from the free
[Open-Meteo](https://open-meteo.com) API to a public dashboard.

**Layers**

| Layer | Schema | Built by |
|---|---|---|
| Raw | `raw` | `pipeline/load.py` (Python) |
| Seeds | `seeds` | `dbt seed` (cities, WMO codes) |
| Staging | `staging` | dbt views |
| Marts | `marts` | dbt tables |

Open the **lineage graph** (bottom-right button) to see how data flows
from the API to `mart_city_summary`.

The whole pipeline runs every day on GitHub Actions and is published to GitHub Pages.
{% enddocs %}
