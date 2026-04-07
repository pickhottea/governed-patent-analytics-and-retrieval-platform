select *
from {{ source('patent_analytics', 'ops_family_members') }}
