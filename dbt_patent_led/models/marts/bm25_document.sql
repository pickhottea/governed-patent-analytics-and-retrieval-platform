select
    a.family_id,
    a.publication_number,
    a.title_jsonl as title,
    a.abstract_jsonl as abstract_text,
    ltrim(rtrim(
        concat(
            coalesce(a.title_jsonl, ''),
            case
                when a.abstract_jsonl is not null and ltrim(rtrim(a.abstract_jsonl)) <> ''
                    then ' ' + a.abstract_jsonl
                else ''
            end
        )
    )) as bm25_text
from {{ ref('stg_publication_abstract_dedup') }} a
where a.publication_number is not null
  and ltrim(rtrim(
        concat(
            coalesce(a.title_jsonl, ''),
            case
                when a.abstract_jsonl is not null and ltrim(rtrim(a.abstract_jsonl)) <> ''
                    then ' ' + a.abstract_jsonl
                else ''
            end
        )
    )) <> ''