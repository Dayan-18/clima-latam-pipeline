-- Dimension: one row per city, enriched with elevation and timezone from the API.
with cities as (

    select * from {{ ref('cities') }}

),

api_attributes as (

    select
        city_id,
        max(elevation_m) as elevation_m,
        max(timezone)    as timezone
    from {{ ref('stg_open_meteo__weather_daily') }}
    group by city_id

)

select
    cities.city_id,
    cities.city_name,
    cities.country,
    cities.country_code,
    cities.latitude,
    cities.longitude,
    api_attributes.elevation_m,
    api_attributes.timezone
from cities
left join api_attributes using (city_id)
