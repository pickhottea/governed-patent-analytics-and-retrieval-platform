select
    upper(ltrim(rtrim(cpc_code))) as cpc_code,
    valid_from_date,
    valid_to_date
from {{ ref('cpc_validity') }}
where cpc_code is not null