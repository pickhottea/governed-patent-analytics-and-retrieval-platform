select distinct
    m.family_id,
    o.ops_family_id as ops_family_cluster_id,
    cast('source_attached' as varchar(50)) as mapping_method,
    cast('high' as varchar(20)) as mapping_confidence,
    cast('raw_pub_to_family_id_v2+ops_family_members' as varchar(100)) as record_source,
    sysutcdatetime() as loaded_at
from {{ ref('stg_raw_pub_to_family_id_v2') }} m
inner join {{ ref('stg_ops_family_members') }} o
    on m.seed_publication_number = o.seed_publication_number
where m.family_id is not null
  and o.ops_family_id is not null
