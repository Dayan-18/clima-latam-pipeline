-- Fact: daily weather per city with derived metrics and a readable description.
with weather as (

    select * from {{ ref('stg_open_meteo__weather_daily') }}

),

codes as (

    select * from {{ ref('weather_codes') }}

)

select
    weather.city_id || '_' || strftime(weather.weather_date, '%Y%m%d') as weather_day_id,
    weather.city_id,
    weather.weather_date,
    weather.temp_max_c,
    weather.temp_min_c,
    round((weather.temp_max_c + weather.temp_min_c) / 2, 1)  as temp_avg_c,
    round(weather.temp_max_c - weather.temp_min_c, 1)         as temp_range_c,
    weather.precipitation_mm,
    weather.wind_max_kmh,
    weather.weather_code,
    coalesce(codes.description, 'Unknown')               as weather_description,
    coalesce(codes.category, 'other')                          as weather_category,
    weather.precipitation_mm >= 1.0                           as is_rainy_day,
    -- today and later come from the forecast model, earlier days are observed
    weather.weather_date >= cast(weather.extracted_at as date) as is_forecast,
    weather.extracted_at
from weather
left join codes on weather.weather_code = codes.weather_code
