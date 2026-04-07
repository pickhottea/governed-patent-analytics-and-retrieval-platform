{{ config(
    materialized='table'
) }}

with bridge as (

    select
        family_id,
        publication_number
    from {{ ref('bridge_family_publication') }}

),

cleaned as (

    select
        family_id,
        ltrim(rtrim(
            replace(
                replace(
                    replace(publication_number, char(13), ''),
                char(10), ''),
            char(9), '')
        )) as publication_number_clean
    from bridge
    where publication_number is not null
      and ltrim(rtrim(publication_number)) <> ''

),

parsed as (

    select
        family_id,
        publication_number_clean as publication_number,
        upper(left(publication_number_clean, 2)) as authority_code
    from cleaned
    where publication_number_clean <> ''

)

select
    p.family_id,
    p.publication_number,
    p.authority_code,
    coalesce(d.country_code, p.authority_code) as country_code,
    coalesce(d.country_name, p.authority_code) as country_name,
    coalesce(d.region_name, 'Unknown') as region_name,
    coalesce(d.is_pragmatic_fill, cast(1 as bit)) as is_pragmatic_fill
from parsed p
left join {{ ref('dim_country') }} d
    on p.authority_code = d.authority_code