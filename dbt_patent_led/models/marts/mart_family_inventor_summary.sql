{{ config(
    materialized='table'
) }}

with src as (

    select
        family_id,
        publication_number,
        inventor_name,
        inventor_country_code_raw
    from {{ ref('mart_publication_inventor_expanded') }}

),

family_dedup as (

    select distinct
        family_id,
        inventor_name,
        inventor_country_code_raw
    from src

)

select
    family_id,
    inventor_name,
    inventor_country_code_raw,
    count(*) as family_inventor_record_count
from family_dedup
group by
    family_id,
    inventor_name,
    inventor_country_code_raw