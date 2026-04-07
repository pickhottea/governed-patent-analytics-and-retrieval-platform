{{ config(
    materialized='table'
) }}

with bridge as (

    select
        family_id,
        publication_number
    from {{ ref('bridge_family_publication') }}

),

cleaned_bridge as (

    select
        family_id,
        ltrim(rtrim(
            replace(
                replace(
                    replace(publication_number, char(13), ''),
                char(10), ''),
            char(9), '')
        )) as publication_number
    from bridge
    where publication_number is not null
      and ltrim(rtrim(publication_number)) <> ''

),

inventor_raw as (

    select
        ltrim(rtrim(
            replace(
                replace(
                    replace(publication_number, char(13), ''),
                char(10), ''),
            char(9), '')
        )) as publication_number,

        inventor_seq,

        ltrim(rtrim(
            replace(
                replace(
                    replace(
                        replace(
                            replace(inventor_name_raw, '[', ''),
                        ']', ''),
                    '"', ''),
                char(13), ''),
            char(10), '')
        )) as inventor_name,

        ltrim(rtrim(
            replace(
                replace(
                    replace(inventor_country_code_raw, char(13), ''),
                char(10), ''),
            char(9), '')
        )) as inventor_country_code_raw

    from {{ ref('fact_publication_inventor') }}

),

final as (

    select
        b.family_id,
        b.publication_number,
        i.inventor_seq,
        i.inventor_name,
        i.inventor_country_code_raw
    from cleaned_bridge b
    left join inventor_raw i
        on b.publication_number = i.publication_number

)

select *
from final
where inventor_name is not null
  and ltrim(rtrim(inventor_name)) <> ''