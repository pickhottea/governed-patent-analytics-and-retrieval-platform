select *
from {{ ref('stg_ops_family_members_canonical') }}
where publication_number like '%' + char(123) + '%'
   or publication_number like '%' + char(125) + '%'
   or publication_number like '%' + char(58) + '%'
   or publication_number like '%' + char(36) + '%'
   or publication_number like '%' + char(39) + '%'
   or publication_number like '% %'