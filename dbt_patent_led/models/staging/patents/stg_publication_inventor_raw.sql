select
    family_id,
    publication_number,
    inventor_seq,
    inventor_raw,
    inventor_name_raw,
    inventor_country_code_raw
from {{ source('patent_analytics', 'publication_inventor_raw') }}