select
    family_id,
    sum(case when member_role = 'anchor' then 1 else 0 end) as anchor_publication_count,
    sum(case when member_role = 'expanded_member' then 1 else 0 end) as expanded_member_count,
    count(*) as total_publication_count
from {{ ref('bridge_family_publication') }}
group by family_id