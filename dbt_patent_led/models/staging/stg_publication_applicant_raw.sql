select
    family_id,
    publication_number,
    applicant_seq,
    applicant_raw,
    applicant_name_raw,
    applicant_country_code_raw
from {{ source('patent_analytics', 'publication_applicant_raw') }}