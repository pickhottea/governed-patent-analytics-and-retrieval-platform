with anchor_side as (
    select
        family_id,
        publication_number,
        cast('anchor' as varchar(30)) as member_role,
        cast(null as varchar(100)) as ops_family_cluster_id,
        cast(1 as bit) as is_bm25_representative,
        cast('anchor_rawdata_patents' as varchar(50)) as record_source
    from {{ ref('stg_rawdata_patents') }}
    where family_id is not null
      and publication_number is not null
),
expanded_side as (
    select
        bfo.family_id,
        coalesce(ofm.member_publication_number, ofm.member_publication_docdb) as publication_number,
        cast('expanded_member' as varchar(30)) as member_role,
        cast(bfo.ops_family_cluster_id as varchar(100)) as ops_family_cluster_id,
        cast(0 as bit) as is_bm25_representative,
        cast('ops_family_members' as varchar(50)) as record_source
    from {{ ref('bridge_family_ops_cluster') }} bfo
    inner join {{ ref('stg_ops_family_members') }} ofm
        on bfo.ops_family_cluster_id = ofm.ops_family_id
    where bfo.family_id is not null
      and coalesce(ofm.member_publication_number, ofm.member_publication_docdb) is not null
),
unioned as (
    select * from anchor_side
    union all
    select * from expanded_side
),
deduped as (
    select
        family_id,
        publication_number,
        case
            when max(case when member_role = 'anchor' then 1 else 0 end) = 1
                then 'anchor'
            else 'expanded_member'
        end as member_role,
        max(ops_family_cluster_id) as ops_family_cluster_id,
        cast(max(case when is_bm25_representative = 1 then 1 else 0 end) as bit) as is_bm25_representative,
        case
            when count(distinct record_source) > 1 then 'anchor+ops_expansion'
            else max(record_source)
        end as record_source
    from unioned
    group by family_id, publication_number
),
publication_collision as (
    select
        publication_number,
        count(distinct family_id) as publication_family_count
    from deduped
    group by publication_number
)
select
    d.family_id,
    d.publication_number,
    d.member_role,
    d.ops_family_cluster_id,
    d.is_bm25_representative,
    cast(case when isnull(pc.publication_family_count, 1) > 1 then 1 else 0 end as bit) as has_publication_collision,
    case
        when isnull(pc.publication_family_count, 1) > 1 then 'FAMILY_TO_PUBLICATION_COLLISION'
        else null
    end as collision_flag,
    d.record_source,
    sysutcdatetime() as loaded_at
from deduped d
left join publication_collision pc
    on d.publication_number = pc.publication_number
