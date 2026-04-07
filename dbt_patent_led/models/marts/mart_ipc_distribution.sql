select
    bfp.family_id,
    bpi.publication_number,
    bpi.ipc_code,
    di.ipc_section,
    di.ipc_class,
    di.ipc_subclass,
    di.ipc_group,
    di.ipc_subgroup
from {{ ref('bridge_publication_ipc') }} as bpi
left join {{ ref('bridge_family_publication') }} as bfp
    on bpi.publication_number = bfp.publication_number
left join {{ ref('dim_ipc') }} as di
    on bpi.ipc_code = di.ipc_code