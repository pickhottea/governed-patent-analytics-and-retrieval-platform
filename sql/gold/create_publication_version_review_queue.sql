CREATE TABLE gold.publication_version_review_queue (
    review_id                  BIGINT IDENTITY(1,1) NOT NULL,
    family_id                  VARCHAR(32)     NULL,
    publication_number         VARCHAR(64)     NOT NULL,
    publication_number_norm    VARCHAR(64)     NULL,
    authority_code             VARCHAR(8)      NULL,
    base_number                VARCHAR(32)     NULL,
    kind_code                  VARCHAR(8)      NULL,

    matched_publication_number VARCHAR(64)     NULL,
    matched_publication_norm   VARCHAR(64)     NULL,
    matched_authority_code     VARCHAR(8)      NULL,
    matched_base_number        VARCHAR(32)     NULL,
    matched_kind_code          VARCHAR(8)      NULL,

    review_reason              VARCHAR(100)    NOT NULL,
    review_status              VARCHAR(30)     NOT NULL CONSTRAINT DF_pub_ver_review_status DEFAULT ('pending'),
    reviewer_note              NVARCHAR(1000)  NULL,
    source_table               VARCHAR(128)    NULL,
    created_at                 DATETIME2(6)    NOT NULL CONSTRAINT DF_pub_ver_review_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at                 DATETIME2(6)    NOT NULL CONSTRAINT DF_pub_ver_review_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_publication_version_review_queue
        PRIMARY KEY (review_id),

    CONSTRAINT CK_publication_version_review_status
        CHECK (review_status IN ('pending', 'approved_merge', 'approved_keep_separate', 'rejected', 'ignored'))
);
