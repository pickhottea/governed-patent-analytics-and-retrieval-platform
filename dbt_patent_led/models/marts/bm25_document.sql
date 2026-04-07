select
    r.family_id,
    r.publication_number,
    r.title,
    a.abstract_jsonl as abstract_text,
    ltrim(rtrim(
        concat(
            coalesce(r.title, ''),
            case
                when a.abstract_jsonl is not null and ltrim(rtrim(a.abstract_jsonl)) <> ''
                    then ' ' + a.abstract_jsonl
                else ''
            end
        )
    )) as bm25_text
from {{ ref('stg_rawdata_patents') }} r
left join {{ ref('stg_publication_abstract_dedup') }} a
    on r.publication_number = a.publication_number
where r.publication_number is not null
  and a.abstract_jsonl is not null
  and ltrim(rtrim(a.abstract_jsonl)) <> ''