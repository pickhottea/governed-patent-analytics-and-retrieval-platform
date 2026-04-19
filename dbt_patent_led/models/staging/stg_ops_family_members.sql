with source_data as (

    select *
    from {{ source('patent_analytics', 'ops_family_members') }}

),

final as (

    select
        ops_family_member_key,
        ops_family_member_row_id,
        ops_family_id,
        seed_publication_number,
        seed_publication_docdb,
        family_members_count,
        member_seq_within_ops_family,
        member_publication_docdb,
        member_publication_number,
        member_jurisdiction,
        member_kind,
        source_file_name,
        ingested_at,

        nullif(
            upper(
                replace(
                    replace(
                        replace(
                            replace(
                                replace(
                                    replace(
                                        ltrim(rtrim(cast(member_publication_docdb as varchar(4000)))),
                                        char(123), ''
                                    ),
                                    char(125), ''
                                ),
                                char(58), ''
                            ),
                            char(36), ''
                        ),
                        char(39), ''
                    ),
                    ' ', ''
                )
            ),
            ''
        ) as member_publication_docdb_clean,

        nullif(
            upper(
                replace(
                    replace(
                        replace(
                            replace(
                                replace(
                                    replace(
                                        ltrim(rtrim(cast(member_publication_number as varchar(4000)))),
                                        char(123), ''
                                    ),
                                    char(125), ''
                                ),
                                char(58), ''
                            ),
                            char(36), ''
                        ),
                        char(39), ''
                    ),
                    ' ', ''
                )
            ),
            ''
        ) as member_publication_number_clean

    from source_data

)

select *
from final
