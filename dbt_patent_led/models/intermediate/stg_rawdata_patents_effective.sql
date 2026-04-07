{{ config(materialized='view') }}

select
    family_id,
    publication_number_raw,
    publication_number,
    publication_number_norm,
    grant_number,
    title,
    inventors,
    applicants,
    priority_date,
    application_date,
    publication_date,
    source_file_name,
    ingested_at,
    row_id,
    json_payload
from {{ ref('stg_rawdata_patents') }}

union all

select
    family_id,
    publication_number_raw,
    publication_number,
    publication_number_norm,
    grant_number,
    title,
    inventors,
    applicants,
    priority_date,
    application_date,
    publication_date,
    source_file_name,
    ingested_at,
    row_id,
    json_payload
from {{ ref('stg_rawdata_patents_backfill_gap') }}