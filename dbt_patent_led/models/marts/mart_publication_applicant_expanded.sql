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

applicant_raw as (

    select
        ltrim(rtrim(
            replace(
                replace(
                    replace(publication_number, char(13), ''),
                char(10), ''),
            char(9), '')
        )) as publication_number,
        applicant_seq,

        ltrim(rtrim(
            replace(
                replace(
                    replace(
                        replace(
                            replace(applicant_name_raw, '[', ''),
                        ']', ''),
                    '"', ''),
                char(13), ''),
            char(10), '')
        )) as applicant_name,

        ltrim(rtrim(
            replace(
                replace(
                    replace(applicant_country_code_raw, char(13), ''),
                char(10), ''),
            char(9), '')
        )) as applicant_country_code_raw

    from {{ ref('fact_publication_applicant') }}

),

final as (

    select
        b.family_id,
        b.publication_number,
        a.applicant_seq,
        a.applicant_name,
        a.applicant_country_code_raw
    from cleaned_bridge b
    left join applicant_raw a
        on b.publication_number = a.publication_number

)

select *
from final
where applicant_name is not null
  and ltrim(rtrim(applicant_name)) <> ''