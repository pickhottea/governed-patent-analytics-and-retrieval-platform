{{ config(materialized='table') }}

with anchor_side as (

    select
        rp.family_id,
        rp.publication_number_norm as publication_number,
        rp.publication_number_raw,
        rp.publication_number_norm,
        cast('anchor' as varchar(30)) as member_role,
        cast(null as varchar(100)) as ops_family_cluster_id,
        cast(1 as bit) as is_bm25_representative,
        cast('anchor_rawdata_patents' as varchar(50)) as record_source
    from {{ ref('stg_rawdata_patents') }} rp
    where rp.family_id is not null
      and rp.publication_number_norm is not null

),

anchor_keys as (

    select distinct
        family_id,
        publication_number_norm
    from anchor_side

),

anchor_publication_owner as (

    select
        publication_number_norm,
        min(cast(family_id as varchar(100))) as anchor_family_id,
        count(distinct family_id) as anchor_family_count
    from anchor_side
    group by publication_number_norm

),

ops_members_normalized as (

    select
        ofm.ops_family_id,
        ofm.ops_family_cluster_id,
        ofm.member_publication_number as member_publication_number_raw,
        ofm.publication_number as member_publication_number_norm
    from {{ ref('stg_ops_family_members_canonical') }} ofm
    where ofm.publication_number is not null

),

expanded_candidates as (

    select distinct
        bfo.family_id,
        om.member_publication_number_norm as publication_number,
        om.member_publication_number_raw as publication_number_raw,
        om.member_publication_number_norm as publication_number_norm,
        cast(bfo.ops_family_cluster_id as varchar(100)) as ops_family_cluster_id
    from {{ ref('bridge_family_ops_cluster') }} bfo
    inner join ops_members_normalized om
        on cast(bfo.ops_family_cluster_id as varchar(100)) = cast(om.ops_family_cluster_id as varchar(100))
    where bfo.family_id is not null
      and om.member_publication_number_norm is not null

),

expanded_minus_same_family_anchor as (

    select
        ec.family_id,
        ec.publication_number,
        ec.publication_number_raw,
        ec.publication_number_norm,
        ec.ops_family_cluster_id
    from expanded_candidates ec
    left join anchor_keys ak
        on cast(ec.family_id as varchar(100)) = cast(ak.family_id as varchar(100))
       and ec.publication_number_norm = ak.publication_number_norm
    where ak.publication_number_norm is null

),

expanded_family_counts as (

    select
        publication_number_norm,
        count(distinct family_id) as expanded_family_count
    from expanded_minus_same_family_anchor
    group by publication_number_norm

),

expanded_allowed as (

    select
        ema.family_id,
        ema.publication_number,
        ema.publication_number_raw,
        ema.publication_number_norm,
        cast('expanded_member' as varchar(30)) as member_role,
        ema.ops_family_cluster_id,
        cast(0 as bit) as is_bm25_representative,
        cast('ops_family_members' as varchar(50)) as record_source
    from expanded_minus_same_family_anchor ema
    left join expanded_family_counts efc
        on ema.publication_number_norm = efc.publication_number_norm
    left join anchor_publication_owner apo
        on ema.publication_number_norm = apo.publication_number_norm
    where isnull(efc.expanded_family_count, 0) = 1
      and (
            apo.publication_number_norm is null
            or apo.anchor_family_id = cast(ema.family_id as varchar(100))
          )

),

final_rows as (

    select
        family_id,
        publication_number,
        publication_number_raw,
        publication_number_norm,
        member_role,
        ops_family_cluster_id,
        is_bm25_representative,
        record_source
    from anchor_side

    union all

    select
        family_id,
        publication_number,
        publication_number_raw,
        publication_number_norm,
        member_role,
        ops_family_cluster_id,
        is_bm25_representative,
        record_source
    from expanded_allowed

),

publication_collision as (

    select
        publication_number,
        count(distinct family_id) as publication_family_count
    from final_rows
    group by publication_number

)

select
    f.family_id,
    f.publication_number,
    f.publication_number_raw,
    f.publication_number_norm,
    f.member_role,
    f.ops_family_cluster_id,
    f.is_bm25_representative,
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
    f.record_source,
    sysutcdatetime() as loaded_at
from final_rows f
left join publication_collision pc
    on f.publication_number = pc.publication_number