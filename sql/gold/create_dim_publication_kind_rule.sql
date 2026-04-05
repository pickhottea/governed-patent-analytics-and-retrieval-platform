CREATE TABLE gold.dim_publication_kind_rule (
    authority_code                VARCHAR(8)    NOT NULL,
    kind_code                     VARCHAR(8)    NOT NULL,
    kind_prefix                   VARCHAR(2)    NULL,
    office_semantic_group         VARCHAR(50)   NULL,
    exact_dedup_allowed           BIT           NOT NULL CONSTRAINT DF_dim_pub_kind_exact_dedup DEFAULT (1),
    cross_kind_auto_dedup_allowed BIT           NOT NULL CONSTRAINT DF_dim_pub_kind_cross_kind_dedup DEFAULT (0),
    requires_manual_review        BIT           NOT NULL CONSTRAINT DF_dim_pub_kind_manual_review DEFAULT (0),
    rule_status                   VARCHAR(30)   NOT NULL CONSTRAINT DF_dim_pub_kind_rule_status DEFAULT ('active'),
    notes                         NVARCHAR(500) NULL,
    created_at                    DATETIME2(6)  NOT NULL CONSTRAINT DF_dim_pub_kind_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at                    DATETIME2(6)  NOT NULL CONSTRAINT DF_dim_pub_kind_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_dim_publication_kind_rule
        PRIMARY KEY (authority_code, kind_code),

    CONSTRAINT CK_dim_publication_kind_rule_status
        CHECK (rule_status IN ('active', 'manual_review_only', 'out_of_scope_v1'))
);
