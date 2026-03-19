select
    applicant_name_raw,
    applicant_country_code_raw,
    count(distinct publication_number) as publication_count
from {{ ref('fact_publication_applicant') }}
group by
    applicant_name_raw,
    applicant_country_code_raw