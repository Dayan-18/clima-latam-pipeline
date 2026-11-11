-- Staging: rename, cast and clean the raw API data. One row per city per day.
with source as (

    select * from {{ source('open_meteo', 'weather_daily') }}

),

renamed as (

    select
        city_id,
        cast(weather_date as date)                     as weather_date,
        round(temperature_2m_max, 1)                   as temp_max_c,
        round(temperature_2m_min, 1)                   as temp_min_c,
        round(coalesce(precipitation_sum, 0), 1)       as precipitation_mm,
        round(wind_speed_10m_max, 1)                   as wind_max_kmh,
        cast(weather_code as integer)                  as weather_code,
        cast(elevation as integer)                     as elevation_m,
        timezone,
        cast(extracted_at as timestamp)                as extracted_at
    from source
    -- the API can return empty values at the edge of the forecast window
    where temperature_2m_max is not null
      and temperature_2m_min is not null

)

select * from renamed
