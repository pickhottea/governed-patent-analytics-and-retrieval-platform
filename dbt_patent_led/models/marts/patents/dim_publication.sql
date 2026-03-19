select distinct
    publication_number
from {{ ref('bridge_family_publication') }}
where publication_number is not null