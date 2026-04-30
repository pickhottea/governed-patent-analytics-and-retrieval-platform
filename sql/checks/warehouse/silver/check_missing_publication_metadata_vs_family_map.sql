select
    m.family_id,
    m.publication_number
from dbo.stg_raw_pub_to_family_id_v2 m
left join dbo.stg_rawdata_patents p
    on m.publication_number = p.publication_number
where p.publication_number is null
order by m.family_id, m.publication_number;
