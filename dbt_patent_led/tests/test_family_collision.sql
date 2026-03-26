with collisions as (
    select
        publication_number,
        count(distinct family_id) as family_cnt
    from {{ ref('bridge_family_publication') }}
    group by publication_number
)
select *
from collisions
where family_cnt > 1