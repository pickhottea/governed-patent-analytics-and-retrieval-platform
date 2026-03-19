select distinct
    publication_number,
    ipc_token_clean as ipc_code
from {{ ref('stg_publication_ipc') }}
where publication_number is not null
  and ipc_token_clean is not null