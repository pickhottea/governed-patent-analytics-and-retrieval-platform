{{ config(
    materialized='table'
) }}

select
    upper(ltrim(rtrim(authority_code))) as authority_code,
    upper(ltrim(rtrim(country_code))) as country_code,
    country_name,
    region_name,
    cast(is_pragmatic_fill as bit) as is_pragmatic_fill
from {{ ref('country_authority_lookup') }}