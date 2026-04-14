select
    upper(ltrim(rtrim(ipc_code_raw))) as ipc_code,
    nullif(ltrim(rtrim(hierarchy_level_raw)), '') as hierarchy_level_raw,
    ltrim(rtrim(title_text)) as title_text,
    source_file
from {{ ref('ipc_title_list') }}
where ipc_code_raw is not null