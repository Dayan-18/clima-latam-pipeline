-- Singular test: the daily maximum can never be lower than the minimum.
-- Any row returned here makes `dbt build` fail and stops the deploy.
select
    weather_day_id,
    temp_max_c,
    temp_min_c
from {{ ref('fct_weather_daily') }}
where temp_max_c < temp_min_c
