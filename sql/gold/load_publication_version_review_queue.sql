/*
File: sql/gold/load_publication_version_review_queue.sql
Purpose:
  Populate gold.publication_version_review_queue from
  gold.v_publication_version_candidate.

Policy summary:
  - V1 automatic rule coverage: WO / EP / US only
  - Exact same publication identity is not queued here
  - Same base + different kind within WO/EP/US => manual review
  - WO/EP/US rows with missing or unmapped kind rules => manual review
  - Non-WO/EP/US authorities => out-of-scope V1 manual review

Notes:
  - Current candidate view intentionally reads from dbo.dim_publication
    because gold.dim_publication is currently empty in the working DB.
  - This script is publication-version review only.
    It is NOT a family-expansion gate.
*/

SET NOCOUNT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Reset queue for a clean rebuild of the current review snapshot.
    TRUNCATE TABLE gold.publication_version_review_queue;

    /*
    Queue A
    Same authority + same base_number + different kind_code
    within the formal V1 scope (WO / EP / US).
    */
    INSERT INTO gold.publication_version_review_queue
    (
        family_id,
        publication_number,
        publication_number_norm,
        authority_code,
        base_number,
        kind_code,
        matched_publication_number,
        matched_publication_norm,
        matched_authority_code,
        matched_base_number,
        matched_kind_code,
        review_reason,
        source_table
    )
    SELECT
        NULL AS family_id,
        a.publication_number,
        a.publication_number_norm,
        a.authority_code,
        a.base_number,
        a.kind_code,
        b.publication_number,
        b.publication_number_norm,
        b.authority_code,
        b.base_number,
        b.kind_code,
        'same_base_different_kind',
        'gold.v_publication_version_candidate'
    FROM gold.v_publication_version_candidate a
    JOIN gold.v_publication_version_candidate b
      ON a.authority_code = b.authority_code
     AND a.base_number = b.base_number
     AND a.publication_number_norm < b.publication_number_norm
     AND ISNULL(a.kind_code, '') <> ISNULL(b.kind_code, '')
    WHERE a.authority_code IN ('WO', 'EP', 'US')
      AND a.base_number IS NOT NULL;

    /*
    Queue B
    In-scope authority, but parsing/rule application is not ready.
    This catches WO/EP/US rows with null authority/base/kind or
    rows whose kind_code is not found in dim_publication_kind_rule.
    */
    INSERT INTO gold.publication_version_review_queue
    (
        family_id,
        publication_number,
        publication_number_norm,
        authority_code,
        base_number,
        kind_code,
        matched_publication_number,
        matched_publication_norm,
        matched_authority_code,
        matched_base_number,
        matched_kind_code,
        review_reason,
        source_table
    )
    SELECT
        NULL AS family_id,
        v.publication_number,
        v.publication_number_norm,
        v.authority_code,
        v.base_number,
        v.kind_code,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        CASE
            WHEN v.authority_code IS NULL OR v.base_number IS NULL OR v.kind_code IS NULL
                THEN 'in_scope_parse_incomplete'
            ELSE 'in_scope_kind_rule_missing'
        END AS review_reason,
        'gold.v_publication_version_candidate'
    FROM gold.v_publication_version_candidate v
    LEFT JOIN gold.dim_publication_kind_rule r
      ON r.authority_code = v.authority_code
     AND r.kind_code = v.kind_code
    WHERE v.authority_code IN ('WO', 'EP', 'US')
      AND (
            v.authority_code IS NULL
         OR v.base_number IS NULL
         OR v.kind_code IS NULL
         OR r.authority_code IS NULL
      );

    /*
    Queue C
    Authority is outside formal V1 rule scope.
    Keep these visible for future expansion (CN, DE, JP, MX, etc.).
    */
    INSERT INTO gold.publication_version_review_queue
    (
        family_id,
        publication_number,
        publication_number_norm,
        authority_code,
        base_number,
        kind_code,
        matched_publication_number,
        matched_publication_norm,
        matched_authority_code,
        matched_base_number,
        matched_kind_code,
        review_reason,
        source_table
    )
    SELECT
        NULL AS family_id,
        v.publication_number,
        v.publication_number_norm,
        v.authority_code,
        v.base_number,
        v.kind_code,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        'authority_out_of_scope_v1',
        'gold.v_publication_version_candidate'
    FROM gold.v_publication_version_candidate v
    WHERE v.authority_code IS NULL
       OR v.authority_code NOT IN ('WO', 'EP', 'US');

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;

-- Quick verification
SELECT
    review_reason,
    COUNT(*) AS cnt
FROM gold.publication_version_review_queue
GROUP BY review_reason
ORDER BY cnt DESC, review_reason;
