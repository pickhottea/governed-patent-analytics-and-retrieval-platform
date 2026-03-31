{{ config(materialized='view') }}

with anchor_side as (
    select
        rp.family_id,
        rp.publication_number as anchor_publication_number,
        upper(left(rp.publication_number, 2)) as anchor_jurisdiction,
        cast('anchor' as varchar(30)) as member_role,
        cast(null as varchar(100)) as ops_family_cluster_id,
        cast(1 as bit) as is_bm25_representative,
        cast('anchor_rawdata_patents' as varchar(50)) as record_source,
        cast(null as varchar(100)) as expansion_gate_rule
    from {{ ref('stg_rawdata_patents') }} rp
    where rp.family_id is not null
      and rp.publication_number is not null
),

ops_members_normalized as (
    select
        ofm.ops_family_member_key,
        ofm.ops_family_member_row_id,
        ofm.ops_family_id,
        ofm.seed_publication_number,
        ofm.seed_publication_docdb,
        ofm.family_members_count,
        ofm.member_seq_within_ops_family,
        ofm.member_publication_number,
        ofm.member_publication_docdb,
        ofm.member_jurisdiction,
        ofm.member_kind,
        ofm.source_file_name,
        ofm.ingested_at,

        upper(nullif(ofm.member_jurisdiction, '')) as member_jurisdiction_norm,
        upper(nullif(ofm.member_kind, '')) as member_kind_norm,

        case
            when patindex('%[0-9]%', ofm.member_publication_number) > 0
            then substring(
                ofm.member_publication_number,
                patindex('%[0-9]%', ofm.member_publication_number),
                len(ofm.member_publication_number)
            )
            when patindex('%[0-9]%', ofm.member_publication_docdb) > 0
            then substring(
                ofm.member_publication_docdb,
                patindex('%[0-9]%', ofm.member_publication_docdb),
                len(ofm.member_publication_docdb)
            )
            else null
        end as publication_tail_raw
    from {{ ref('stg_ops_family_members') }} ofm
),

ops_members_resolved as (
    select
        om.*,

        case
            when om.publication_tail_raw is null then null
            when patindex('%[^0-9]%', om.publication_tail_raw) = 0
                then om.publication_tail_raw
            else left(
                om.publication_tail_raw,
                patindex('%[^0-9]%', om.publication_tail_raw) - 1
            )
        end as publication_number_numeric_part,

        case
            when om.member_jurisdiction_norm is not null
             and om.member_kind_norm is not null
             and (
                    case
                        when om.publication_tail_raw is null then null
                        when patindex('%[^0-9]%', om.publication_tail_raw) = 0
                            then om.publication_tail_raw
                        else left(
                            om.publication_tail_raw,
                            patindex('%[^0-9]%', om.publication_tail_raw) - 1
                        )
                    end
                 ) is not null
            then
                om.member_jurisdiction_norm +
                (
                    case
                        when om.publication_tail_raw is null then null
                        when patindex('%[^0-9]%', om.publication_tail_raw) = 0
                            then om.publication_tail_raw
                        else left(
                            om.publication_tail_raw,
                            patindex('%[^0-9]%', om.publication_tail_raw) - 1
                        )
                    end
                ) +
                om.member_kind_norm
            else null
        end as member_publication_number_resolved,

        coalesce(
            om.member_jurisdiction_norm,
            left(om.seed_publication_number, 2)
        ) as member_jurisdiction_resolved
    from ops_members_normalized om
),

expanded_candidates as (
    select
        a.family_id,
        omr.member_publication_number_resolved as publication_number,
        cast('expanded_member' as varchar(30)) as member_role,
        cast(bfo.ops_family_cluster_id as varchar(100)) as ops_family_cluster_id,
        cast(0 as bit) as is_bm25_representative,
        cast('ops_family_members' as varchar(50)) as record_source,
        cast('same_jurisdiction_as_anchor' as varchar(100)) as expansion_gate_rule,
        a.anchor_jurisdiction,
        omr.member_jurisdiction_resolved
    from anchor_side a
    inner join {{ ref('bridge_family_ops_cluster') }} bfo
        on a.family_id = bfo.family_id
    inner join ops_members_resolved omr
        on bfo.ops_family_cluster_id = omr.ops_family_id
    where omr.member_publication_number_resolved is not null
),

expanded_side as (
    select
        ec.family_id,
        ec.publication_number,
        ec.member_role,
        ec.ops_family_cluster_id,
        ec.is_bm25_representative,
        ec.record_source,
        ec.expansion_gate_rule
    from expanded_candidates ec
    where ec.member_jurisdiction_resolved = ec.anchor_jurisdiction
),

unioned as (
    select
        a.family_id,
        a.anchor_publication_number as publication_number,
        a.member_role,
        a.ops_family_cluster_id,
        a.is_bm25_representative,
        a.record_source,
        a.expansion_gate_rule
    from anchor_side a

    union all

    select
        e.family_id,
        e.publication_number,
        e.member_role,
        e.ops_family_cluster_id,
        e.is_bm25_representative,
        e.record_source,
        e.expansion_gate_rule
    from expanded_side e
),

deduped as (
    select
        u.family_id,
        u.publication_number,
        case
            when max(case when u.member_role = 'anchor' then 1 else 0 end) = 1
                then 'anchor'
            else 'expanded_member'
        end as member_role,
        max(u.ops_family_cluster_id) as ops_family_cluster_id,
        cast(
            max(case when u.is_bm25_representative = 1 then 1 else 0 end)
            as bit
        ) as is_bm25_representative,
        case
            when count(distinct u.record_source) > 1 then 'anchor+ops_expansion'
            else max(u.record_source)
        end as record_source,
        case
            when max(case when u.member_role = 'anchor' then 1 else 0 end) = 1
                then null
            else max(u.expansion_gate_rule)
        end as expansion_gate_rule
    from unioned u
    group by
        u.family_id,
        u.publication_number
),

publication_collision as (
    select
        d.publication_number,
        count(distinct d.family_id) as publication_family_count
    from deduped d
    group by
        d.publication_number
)

select
    d.family_id,
    d.publication_number,
    d.member_role,
    d.ops_family_cluster_id,
    d.is_bm25_representative,
    cast(
        case
            when isnull(pc.publication_family_count, 1) > 1 then 1
            else 0
        end
        as bit
    ) as has_publication_collision,
    case
        when isnull(pc.publication_family_count, 1) > 1
            then 'FAMILY_TO_PUBLICATION_COLLISION'
        else null
    end as collision_flag,
    d.record_source,
    d.expansion_gate_rule,
    sysutcdatetime() as loaded_at
from deduped d
left join publication_collision pc
    on d.publication_number = pc.publication_number