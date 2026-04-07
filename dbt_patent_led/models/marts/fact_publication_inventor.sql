select
    publication_number,
    inventor_seq,
    inventor_name_raw,
    inventor_country_code_raw
from {{ ref('stg_publication_inventor_raw') }}