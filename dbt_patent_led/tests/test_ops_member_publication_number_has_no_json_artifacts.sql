select *
from {{ ref('stg_ops_family_members') }}
where member_publication_number like '%' + char(123) + '%'
   or member_publication_number like '%' + char(125) + '%'
   or member_publication_number like '%' + char(58) + '%'
   or member_publication_number like '%' + char(36) + '%'
   or member_publication_number like '%' + char(39) + '%'
   or member_publication_number like '% %'