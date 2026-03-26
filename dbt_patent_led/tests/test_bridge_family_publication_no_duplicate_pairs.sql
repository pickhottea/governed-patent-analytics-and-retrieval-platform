with dup_pairs as (
    select
        family_id,
        publication_number,
        count(*) as row_cnt
    from {{ ref('bridge_family_publication') }}
    group by family_id, publication_number
)
select *
from dup_pairs
where row_cnt > 1