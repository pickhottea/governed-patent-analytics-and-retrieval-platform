-- models/marts/patents/mart_family_ipc_distribution.sql

{{ config(materialized='table') }}

with publication_ipc_expanded as (

    select *
    from {{ ref('mart_publication_ipc_expanded') }}

),

family_ipc as (

    select distinct
        family_id,
        ipc_code,
        ipc_section,
        ipc_class,
        ipc_subclass,
        ipc_group,
        ipc_subgroup
    from publication_ipc_expanded

),

publication_coverage as (

    select
        family_id,
        ipc_code,
        count(distinct publication_number) as publication_count_with_ipc
    from publication_ipc_expanded
    group by
        family_id,
        ipc_code

)

select
    f.family_id,
    f.ipc_code,
    f.ipc_section,
    f.ipc_class,
    f.ipc_subclass,
    f.ipc_group,
    f.ipc_subgroup,
    c.publication_count_with_ipc
from family_ipc f
left join publication_coverage c
    on f.family_id = c.family_id
   and f.ipc_code = c.ipc_code