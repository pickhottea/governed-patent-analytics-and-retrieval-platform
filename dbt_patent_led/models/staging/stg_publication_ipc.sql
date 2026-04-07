select *
from {{ source('patent_analytics', 'publication_ipc') }}
