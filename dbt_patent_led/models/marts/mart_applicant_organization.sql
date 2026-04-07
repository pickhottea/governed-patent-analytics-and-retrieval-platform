{{ config(
    materialized='table'
) }}

with src as (

    select distinct
        family_id,
        applicant_name,
        applicant_country_code_raw
    from {{ ref('mart_family_applicant_summary') }}

),

org_map as (

    select
        applicant_name,
        organization_group,
        mapping_confidence,
        mapping_rule,
        candidate_group,
        notes
    from {{ ref('applicant_organization_map') }}

),

joined as (

    select
        s.family_id,
        s.applicant_name,
        s.applicant_country_code_raw,

        coalesce(m.organization_group, s.applicant_name) as organization_group,
        coalesce(m.mapping_confidence, 'unmapped') as mapping_confidence,
        coalesce(m.mapping_rule, 'fallback_self') as mapping_rule,
        m.candidate_group,
        m.notes
    from src s
    left join org_map m
        on s.applicant_name = m.applicant_name

)

select
    organization_group,

    count(distinct family_id) as distinct_family_count,
    count(distinct applicant_name) as applicant_variant_count,
    count(distinct applicant_country_code_raw) as distinct_country_code_count,

    count(distinct case when mapping_confidence = 'unmapped' then applicant_name end) as unmapped_variant_count,

    case
        when count(distinct case when mapping_confidence = 'unmapped' then applicant_name end) > 0
            then 'has_unmapped'
        when count(distinct case when mapping_confidence = 'low' then applicant_name end) > 0
            then 'low'
        when count(distinct case when mapping_confidence = 'medium' then applicant_name end) > 0
            then 'medium'
        else 'high'
    end as organization_confidence_status

from joined
group by
    organization_group