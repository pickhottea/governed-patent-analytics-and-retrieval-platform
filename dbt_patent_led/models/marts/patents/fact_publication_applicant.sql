select
    publication_number,
    applicant_seq,
    applicant_name_raw,
    applicant_country_code_raw
from {{ ref('stg_publication_applicant_raw') }}