-- Mart: one row per city comparing the observed period with the 7-day forecast.
with daily as (

    select * from {{ ref('fct_weather_daily') }}

),

observed as (

    select
        city_id,
        min(weather_date)                              as period_start,
        max(weather_date)                              as period_end,
        count(*)                                       as observed_days,
        round(avg(temp_avg_c), 1)                      as avg_temp_c,
        max(temp_max_c)                                as max_temp_c,
        min(temp_min_c)                                as min_temp_c,
        round(avg(temp_range_c), 1)                    as avg_temp_range_c,
        round(sum(precipitation_mm), 1)                as total_precipitation_mm,
        count(*) filter (where is_rainy_day)           as rainy_days,
        max(wind_max_kmh)                              as max_wind_kmh,
        arg_max(weather_date, temp_max_c)              as hottest_day,
        mode(weather_category)                         as dominant_category
    from daily
    where not is_forecast
    group by city_id

),

forecast as (

    select
        city_id,
        round(avg(temp_avg_c), 1)                      as forecast_avg_temp_c,
        round(sum(precipitation_mm), 1)                as forecast_precipitation_mm,
        count(*) filter (where is_rainy_day)           as forecast_rainy_days
    from daily
    where is_forecast
    group by city_id

)

select
    cities.city_id,
    cities.city_name,
    cities.country,
    cities.elevation_m,
    observed.period_start,
    observed.period_end,
    observed.observed_days,
    observed.avg_temp_c,
    observed.max_temp_c,
    observed.min_temp_c,
    observed.avg_temp_range_c,
    observed.total_precipitation_mm,
    observed.rainy_days,
    observed.max_wind_kmh,
    observed.hottest_day,
    observed.dominant_category,
    forecast.forecast_avg_temp_c,
    forecast.forecast_precipitation_mm,
    forecast.forecast_rainy_days,
    round(forecast.forecast_avg_temp_c - observed.avg_temp_c, 1) as forecast_temp_delta_c
from {{ ref('dim_cities') }} as cities
left join observed using (city_id)
left join forecast using (city_id)
