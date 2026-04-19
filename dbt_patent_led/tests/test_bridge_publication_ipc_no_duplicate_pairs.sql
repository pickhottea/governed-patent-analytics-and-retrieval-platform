with dupes as (
    select
        publication_number,
        ipc_code,
        count(*) as n
    from {{ ref('bridge_publication_ipc') }}
    group by publication_number, ipc_code
    having count(*) > 1
)
select *
from dupes