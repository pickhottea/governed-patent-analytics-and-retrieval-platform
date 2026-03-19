select distinct
    ipc_token_clean as ipc_code,
    left(ipc_token_clean, 1) as ipc_section,
    left(ipc_token_clean, 3) as ipc_class,
    left(ipc_token_clean, 4) as ipc_subclass,
    case
        when charindex('/', ipc_token_clean) > 0
            then left(ipc_token_clean, charindex('/', ipc_token_clean) - 1)
        else ipc_token_clean
    end as ipc_group,
    case
        when charindex('/', ipc_token_clean) > 0
            then substring(ipc_token_clean, charindex('/', ipc_token_clean) + 1, 50)
        else null
    end as ipc_subgroup
from {{ ref('stg_publication_ipc') }}
where ipc_token_clean is not null