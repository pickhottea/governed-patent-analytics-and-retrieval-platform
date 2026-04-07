{{ config(
    materialized='table'
) }}

with src as (

    select
        family_id,
        publication_number,
        applicant_name,
        applicant_country_code_raw
    from {{ ref('mart_publication_applicant_expanded') }}

),

family_dedup as (

    select distinct
        family_id,
        applicant_name,
        applicant_country_code_raw
    from src

)

select
    family_id,
    applicant_name,
    applicant_country_code_raw,
    count(*) as family_applicant_record_count
from family_dedup
group by
    family_id,
    applicant_name,
    applicant_country_code_raw