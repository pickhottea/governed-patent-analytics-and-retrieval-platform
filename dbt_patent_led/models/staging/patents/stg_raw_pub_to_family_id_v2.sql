select *
from {{ source('patent_analytics', 'raw_pub_to_family_id_v2') }}
