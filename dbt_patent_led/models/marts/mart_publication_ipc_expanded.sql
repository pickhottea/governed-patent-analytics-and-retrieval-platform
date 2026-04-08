-- models/marts/patents/mart_publication_ipc_expanded.sql

{{ config(materialized='table') }}

with family_publication as (

    select
        fp.family_id,
        upper(
            replace(
                replace(
                    replace(
                        ltrim(rtrim(fp.publication_number)),
                        char(9), ''
                    ),
                    char(10), ''
                ),
                char(13), ''
            )
        ) as publication_number
    from {{ ref('bridge_family_publication') }} fp
    where fp.family_id is not null
      and fp.publication_number is not null

),

publication_ipc as (

    select
        upper(
            replace(
                replace(
                    replace(
                        ltrim(rtrim(pi.publication_number)),
                        char(9), ''
                    ),
                    char(10), ''
                ),
                char(13), ''
            )
        ) as publication_number,
        upper(ltrim(rtrim(pi.ipc_code))) as ipc_code
    from {{ ref('bridge_publication_ipc') }} pi
    where pi.publication_number is not null
      and pi.ipc_code is not null

),

ipc_dim as (

    select
        upper(ltrim(rtrim(di.ipc_code))) as ipc_code,
        di.ipc_section,
        di.ipc_class,
        di.ipc_subclass,
        di.ipc_group,
        di.ipc_subgroup
    from {{ ref('dim_ipc') }} di

),

joined as (

    select distinct
        fp.family_id,
        fp.publication_number,
        pi.ipc_code,
        di.ipc_section,
        di.ipc_class,
        di.ipc_subclass,
        di.ipc_group,
        di.ipc_subgroup
    from family_publication fp
    inner join publication_ipc pi
        on fp.publication_number = pi.publication_number
    left join ipc_dim di
        on pi.ipc_code = di.ipc_code

)

select *
from joined