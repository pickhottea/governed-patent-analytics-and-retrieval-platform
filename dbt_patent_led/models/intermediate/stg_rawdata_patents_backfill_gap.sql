{{ config(materialized='view') }}

with ref_pub as (

    select distinct
        family_id,
        publication_number
    from {{ ref('stg_raw_pub_to_family_id_v2') }}

),

raw_pub as (

    select distinct
        publication_number
    from {{ ref('stg_rawdata_patents') }}

),

missing as (

    select
        r.family_id,
        r.publication_number
    from ref_pub r
    left join raw_pub p
        on r.publication_number = p.publication_number
    where p.publication_number is null

)

select
    family_id,
    publication_number as publication_number_raw,
    publication_number,
    publication_number as publication_number_norm,
    cast(null as nvarchar(255)) as grant_number,
    cast(null as nvarchar(max)) as title,
    cast(null as nvarchar(max)) as inventors,
    cast(null as nvarchar(max)) as applicants,
    cast(null as date) as priority_date,
    cast(null as date) as application_date,
    cast(null as date) as publication_date,
    cast('backfill_gap_from_stg_raw_pub_to_family_id_v2' as nvarchar(260)) as source_file_name,
    sysutcdatetime() as ingested_at,
    cast(null as bigint) as row_id,
    cast(null as nvarchar(max)) as json_payload
from missing