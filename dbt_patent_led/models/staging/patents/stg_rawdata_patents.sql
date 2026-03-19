select *
from {{ source('patent_analytics', 'rawdata_patents') }}
