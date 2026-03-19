select
    publication_number,
    family_id,
    title,
    abstract_text,
    case when abstract_text is not null then 1 else 0 end as has_abstract_flag
from {{ ref('bm25_document') }}