-- dbt_patent_led/tests/test_serving_lane_gap.sql

with actual as (
    select count(distinct publication_number) as bm25_publication_count
    from {{ ref('bm25_document') }}
),
expected as (
    select 150 as expected_bm25_publication_count
)
select
    a.bm25_publication_count,
    e.expected_bm25_publication_count
from actual a
cross join expected e
where a.bm25_publication_count <> e.expected_bm25_publication_count