select
    upper(ltrim(rtrim(cpc_code_raw))) as cpc_code,
    nullif(ltrim(rtrim(hierarchy_level_raw)), '') as hierarchy_level_raw,
    ltrim(rtrim(title_text)) as title_text,
    source_file
from {{ ref('cpc_title_list') }}
where cpc_code_raw is not null