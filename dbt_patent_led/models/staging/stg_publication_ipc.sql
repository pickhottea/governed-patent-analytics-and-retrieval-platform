select *
from {{ source('patent_analytics', 'stg_publication_ipc') }}
