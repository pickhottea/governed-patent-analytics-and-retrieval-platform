select *
from {{ source('patent_analytics', 'publication_abstract_dedup') }}
