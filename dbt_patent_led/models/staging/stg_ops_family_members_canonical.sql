{{ config(materialized='view') }}

with src as (

    select
        ops_family_member_key,
        ops_family_member_row_id,
        ops_family_id,
        seed_publication_number,
        seed_publication_docdb,
        family_members_count,
        member_seq_within_ops_family,
        member_publication_docdb,
        member_publication_number,
        member_jurisdiction,
        member_kind,
        source_file_name,
        ingested_at
    from silver.ops_family_members

),

normalized as (

    select
        s.ops_family_member_key,
        s.ops_family_member_row_id,
        s.ops_family_id,
        s.seed_publication_number,
        s.seed_publication_docdb,
        s.family_members_count,
        s.member_seq_within_ops_family,
        s.member_publication_docdb,
        s.member_publication_number,
        s.member_jurisdiction,
        s.member_kind,
        s.source_file_name,
        s.ingested_at,
        pub.member_publication_number_norm,
        doc.member_publication_docdb_norm
    from src s

    outer apply (select ltrim(rtrim(cast(s.member_publication_number as nvarchar(255)))) as v) p0
    outer apply (select replace(p0.v, char(123), '') as v) p1
    outer apply (select replace(p1.v, char(125), '') as v) p2
    outer apply (select replace(p2.v, char(39), '') as v) p3
    outer apply (select replace(p3.v, char(34), '') as v) p4
    outer apply (select replace(p4.v, char(36), '') as v) p5
    outer apply (select replace(p5.v, char(58), '') as v) p6
    outer apply (select replace(p6.v, '.', '') as v) p7
    outer apply (select replace(p7.v, '-', '') as v) p8
    outer apply (select replace(p8.v, '/', '') as v) p9
    outer apply (select replace(p9.v, ' ', '') as v) p10
    outer apply (select replace(p10.v, char(9), '') as v) p11
    outer apply (select replace(p11.v, char(10), '') as v) p12
    outer apply (select replace(p12.v, char(13), '') as v) p13
    outer apply (select upper(nullif(p13.v, '')) as member_publication_number_norm) pub

    outer apply (select ltrim(rtrim(cast(s.member_publication_docdb as nvarchar(255)))) as v) d0
    outer apply (select replace(d0.v, char(123), '') as v) d1
    outer apply (select replace(d1.v, char(125), '') as v) d2
    outer apply (select replace(d2.v, char(39), '') as v) d3
    outer apply (select replace(d3.v, char(34), '') as v) d4
    outer apply (select replace(d4.v, char(36), '') as v) d5
    outer apply (select replace(d5.v, char(58), '') as v) d6
    outer apply (select replace(d6.v, '.', '') as v) d7
    outer apply (select replace(d7.v, '-', '') as v) d8
    outer apply (select replace(d8.v, '/', '') as v) d9
    outer apply (select replace(d9.v, ' ', '') as v) d10
    outer apply (select replace(d10.v, char(9), '') as v) d11
    outer apply (select replace(d11.v, char(10), '') as v) d12
    outer apply (select replace(d12.v, char(13), '') as v) d13
    outer apply (select upper(nullif(d13.v, '')) as member_publication_docdb_norm) doc

),

final as (

    select
        ops_family_member_key,
        ops_family_member_row_id,
        ops_family_id,
        cast(ops_family_id as varchar(100)) as ops_family_cluster_id,
        seed_publication_number,
        seed_publication_docdb,
        family_members_count,
        member_seq_within_ops_family,
        member_publication_docdb,
        member_publication_number,
        member_jurisdiction,
        member_kind,

        coalesce(
            member_publication_number_norm,
            member_publication_docdb_norm
        ) as publication_number,

        coalesce(
            member_publication_number_norm,
            member_publication_docdb_norm
        ) as member_publication_number_norm,

        case
            when member_publication_number_norm is not null then 'member_publication_number'
            when member_publication_docdb_norm is not null then 'member_publication_docdb'
            else 'unresolved'
        end as canonicalization_source,

        case
            when member_publication_number like '%' + char(123) + '%'
              or member_publication_number like '%' + char(125) + '%'
              or member_publication_number like '%' + char(58) + '%'
              or member_publication_number like '%' + char(36) + '%'
              or member_publication_number like '%' + char(39) + '%'
            then cast(1 as bit)
            else cast(0 as bit)
        end as raw_fragment_flag,

        source_file_name,
        ingested_at

    from normalized

)

select *
from final
where publication_number is not null
  and publication_number <> ''