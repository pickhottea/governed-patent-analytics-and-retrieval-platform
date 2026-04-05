with bad_rows as (
    select
        family_id,
        publication_number
    from {{ ref('stg_rawdata_patents') }}
    where publication_number like '%' + char(9) + '%'
       or publication_number like '%' + char(10) + '%'
       or publication_number like '%' + char(13) + '%'
       or publication_number like '%' + nchar(160) + '%'
       or publication_number like ' %'
       or publication_number like '% '
)
select *
from bad_rows