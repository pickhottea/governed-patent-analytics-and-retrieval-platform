with source_data as (

    select
        row_id,
        source_file_name,
        json_payload,
        ingested_at
    from bronze.patents_canonical_raw

),

parsed as (

    select
        row_id,
        source_file_name,
        ingested_at,
        json_payload,

        coalesce(
            json_value(json_payload, '$.family_id'),
            json_value(json_payload, '$.dataset_family_id'),
            json_value(json_payload, '$.familyId'),
            json_value(json_payload, '$.datasetFamilyId')
        ) as family_id,

        coalesce(
            json_value(json_payload, '$.publication_number'),
            json_value(json_payload, '$.selected_publication'),
            json_value(json_payload, '$.seed_publication_number'),
            json_value(json_payload, '$.publicationNumber'),
            json_value(json_payload, '$.selectedPublication'),
            json_value(json_payload, '$.seedPublicationNumber')
        ) as publication_number_raw,

        coalesce(
            json_value(json_payload, '$.grant_number'),
            json_value(json_payload, '$.grantNumber')
        ) as grant_number,

        coalesce(
            json_value(json_payload, '$.title'),
            json_value(json_payload, '$.patent_title'),
            json_value(json_payload, '$.title_text'),
            json_value(json_payload, '$.titleText')
        ) as title,

        coalesce(
            json_value(json_payload, '$.inventors'),
            json_query(json_payload, '$.inventors'),
            json_value(json_payload, '$.inventor'),
            json_query(json_payload, '$.inventor_names')
        ) as inventors,

        coalesce(
            json_value(json_payload, '$.applicants'),
            json_query(json_payload, '$.applicants'),
            json_value(json_payload, '$.applicant'),
            json_query(json_payload, '$.applicant_names')
        ) as applicants,

        coalesce(
            json_value(json_payload, '$.priority_date'),
            json_value(json_payload, '$.priorityDate')
        ) as priority_date_raw,

        coalesce(
            json_value(json_payload, '$.application_date'),
            json_value(json_payload, '$.applicationDate')
        ) as application_date_raw,

        coalesce(
            json_value(json_payload, '$.publication_date'),
            json_value(json_payload, '$.publicationDate')
        ) as publication_date_raw
    from source_data

),

cleaned as (

    select
        family_id,

        publication_number_raw,

        upper(
            replace(
                replace(
                    replace(
                        replace(
                            replace(
                                replace(
                                    ltrim(rtrim(publication_number_raw)),
                                    char(9), ''
                                ),
                                char(10), ''
                            ),
                            char(13), ''
                        ),
                        nchar(160), ''
                    ),
                    '.', ''
                ),
                ' ', ''
            )
        ) as publication_number,

        upper(
            replace(
                replace(
                    replace(
                        replace(
                            replace(
                                replace(
                                    ltrim(rtrim(publication_number_raw)),
                                    char(9), ''
                                ),
                                char(10), ''
                            ),
                            char(13), ''
                        ),
                        nchar(160), ''
                    ),
                    '.', ''
                ),
                ' ', ''
            )
        ) as publication_number_norm,

        grant_number,
        title,
        inventors,
        applicants,
        try_convert(date, priority_date_raw) as priority_date,
        try_convert(date, application_date_raw) as application_date,
        try_convert(date, publication_date_raw) as publication_date,
        source_file_name,
        ingested_at,
        row_id,
        json_payload
    from parsed
    where family_id is not null
      and publication_number_raw is not null

)

select *
from cleaned