{{ config(
    materialized='table'
) }}

with src as (

    select
        family_id,
        publication_number,
        authority_code,
        country_code,
        country_name,
        region_name,
        is_pragmatic_fill
    from {{ ref('mart_publication_country_expanded') }}

)

select
    family_id,
    authority_code,
    country_code,
    country_name,
    region_name,
    is_pragmatic_fill,
    count(*) as publication_count_in_country,
    count(distinct publication_number) as distinct_publication_count
from src
group by
    family_id,
    authority_code,
    country_code,
    country_name,
    region_name,
    is_pragmatic_fill