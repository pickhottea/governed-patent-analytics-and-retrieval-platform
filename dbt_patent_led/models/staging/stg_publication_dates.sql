{{ config(
    materialized='view'
) }}

with src as (

    select
        family_id,
        coalesce(
            nullif(publication_number_norm, ''),
            nullif(publication_number, ''),
            publication_number_raw
        ) as publication_number,
        publication_number_raw,
        publication_number_norm,
        grant_number,
        title,

        try_cast(priority_date as date)    as priority_date,
        try_cast(application_date as date) as application_date,
        try_cast(publication_date as date) as publication_date,

        source_file_name,
        ingested_at,
        row_id,
        json_payload
    from {{ ref('stg_rawdata_patents') }}

),

final as (

    select
        family_id,
        publication_number,
        publication_number_raw,
        publication_number_norm,
        grant_number,
        title,

        priority_date,
        application_date,
        publication_date,

        year(priority_date)    as priority_year,
        year(application_date) as application_year,
        year(publication_date) as publication_year,

        case when publication_date is null then 1 else 0 end as is_publication_date_missing,
        case when priority_date is null then 1 else 0 end as is_priority_date_missing,
        case when application_date is null then 1 else 0 end as is_application_date_missing,
        case when grant_number is not null then 1 else 0 end as is_grant_linked,

        case
            when priority_date is not null
             and publication_date is not null
             and priority_date > publication_date
                then 'priority_after_publication'

            when application_date is not null
             and publication_date is not null
             and application_date > publication_date
                then 'application_after_publication'

            else 'ok'
        end as date_order_flag,

        case
            when publication_date is null and grant_number is not null
                then 'missing_pub_date_grant_side'

            when publication_date is null
                then 'missing_pub_date'

            when priority_date is not null
             and publication_date is not null
             and priority_date > publication_date
                then 'invalid_order'

            when application_date is not null
             and publication_date is not null
             and application_date > publication_date
                then 'invalid_order'

            else 'ok'
        end as date_quality_status,

        source_file_name,
        ingested_at,
        row_id,
        json_payload
    from src

)

select *
from final