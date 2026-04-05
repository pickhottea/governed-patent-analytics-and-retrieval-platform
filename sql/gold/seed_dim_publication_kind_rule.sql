/*
V1 scope:
- Formal rule coverage only for WO / EP / US.
- All other authorities should remain out of scope for automatic version decisions
  and should be routed to review.
*/
INSERT INTO gold.dim_publication_kind_rule
(
    authority_code,
    kind_code,
    kind_prefix,
    office_semantic_group,
    exact_dedup_allowed,
    cross_kind_auto_dedup_allowed,
    requires_manual_review,
    rule_status,
    notes
)
VALUES
-- WO / PCT
('WO', 'A1', 'A', 'application',           1, 0, 0, 'active', 'primary serving candidate'),
('WO', 'A2', 'A', 'application',           1, 0, 1, 'active', 'review if paired with A1/A3/A4'),
('WO', 'A3', 'A', 'secondary_publication', 1, 0, 1, 'active', 'secondary/review only'),
('WO', 'A4', 'A', 'secondary_publication', 1, 0, 1, 'active', 'secondary/review only'),
('WO', 'A8', 'A', 'correction',            1, 0, 1, 'active', 'correction/review only'),
('WO', 'A9', 'A', 'correction',            1, 0, 1, 'active', 'correction/review only'),

-- EP
('EP', 'A1', 'A', 'application',           1, 0, 0, 'active', 'primary serving candidate'),
('EP', 'A2', 'A', 'application',           1, 0, 1, 'active', 'review if paired with A1/A3/A4'),
('EP', 'A3', 'A', 'secondary_publication', 1, 0, 1, 'active', 'secondary/review only'),
('EP', 'A4', 'A', 'secondary_publication', 1, 0, 1, 'active', 'secondary/review only'),
('EP', 'A8', 'A', 'correction',            1, 0, 1, 'active', 'correction/review only'),
('EP', 'A9', 'A', 'correction',            1, 0, 1, 'active', 'correction/review only'),
('EP', 'B1', 'B', 'grant',                 1, 0, 1, 'active', 'grant-stage document, do not auto-merge with A'),
('EP', 'B2', 'B', 'grant',                 1, 0, 1, 'active', 'grant-stage document, do not auto-merge with A'),

-- US
('US', 'A1', 'A', 'application',           1, 0, 0, 'active', 'primary serving candidate'),
('US', 'A2', 'A', 'application',           1, 0, 1, 'active', 'review if paired with A1/A9/B'),
('US', 'A9', 'A', 'correction',            1, 0, 1, 'active', 'correction/review only'),
('US', 'B1', 'B', 'grant',                 1, 0, 1, 'active', 'grant-stage document, do not auto-merge with A'),
('US', 'B2', 'B', 'grant',                 1, 0, 1, 'active', 'grant-stage document, do not auto-merge with A');
