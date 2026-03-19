select
    inventor_name_raw,
    inventor_country_code_raw,
    count(distinct publication_number) as publication_count
from {{ ref('fact_publication_inventor') }}
group by
    inventor_name_raw,
    inventor_country_code_raw