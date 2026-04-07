{{ config(
    materialized='view'
) }}

with src as (

    select
        family_id,
        publication_number
    from {{ ref('stg_publication_dates') }}

),

parsed as (

    select
        family_id,
        publication_number,
        upper(left(publication_number, 2)) as authority_code
    from src
    where publication_number is not null

)

select
    p.family_id,
    p.publication_number,
    p.authority_code,
    d.country_code,
    d.country_name,
    d.region_name,
    d.is_pragmatic_fill
from parsed p
left join {{ ref('dim_country') }} d
    on p.authority_code = d.authority_code