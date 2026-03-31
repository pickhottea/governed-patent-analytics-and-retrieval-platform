# Family Expansion Boundary Policy v1

## Purpose

This policy defines how OPS-derived family expansion may be used in the governed patent warehouse.

Its purpose is to prevent uncontrolled expansion from overriding the project’s canonical dataset family identity.

This policy applies to:

- `silver.ops_family_members`
- `gold.bridge_family_ops_cluster`
- `gold.bridge_family_publication`

---

## Core principle

> OPS family expansion is a candidate publication pool, not canonical dataset family identity.

The governed warehouse treats `family_id` as the canonical family key.

Any OPS-derived family expansion is subordinate to that identity and must pass explicit control gates before expanded publications can be attached to a dataset family.

---

## Canonical identity rule

### Canonical family identity

- `family_id` is the governed family key for the warehouse.

### Canonical publication identity

- `publication_number` is the governed publication key for family-publication bridge use.
- OPS-derived publication identifiers must be normalized before entering `gold.bridge_family_publication`.

OPS cluster or OPS family identifiers may support expansion logic, but they must not replace or redefine the warehouse’s canonical dataset family identity.

---

## Expansion policy

### Allowed role of OPS expansion

OPS-derived family expansion may be used only as:

- a candidate publication pool
- a coverage support source
- a diagnostic aid for family expansion review

OPS-derived expansion must not be treated as automatic entitlement to attach all OPS member publications to a dataset family.

---

## Required gates before attachment

An OPS-derived publication may be attached to a dataset family only if it passes all required gates.

### Gate 1 — normalization gate

OPS-derived publication identifiers must be normalized before use in the gold bridge.

At minimum, the bridge must not directly use raw partially parsed values such as:

- `{'$':'EP'}{'$':'3919806'}{'$':'A1'}`
- `{'$':'US'}{'$':'11326744'}{'$':'B2'}`

Instead, a normalized governed publication key must be produced first, such as:

- `EP3919806A1`
- `US11326744B2`

If no valid normalized identifier can be produced, the publication must not enter `gold.bridge_family_publication`.

### Gate 2 — boundary gate

OPS-derived expanded members must pass an explicit family-boundary gate before attachment.

For the current conservative implementation, the boundary gate is:

- `member_jurisdiction = anchor_jurisdiction`

This means a candidate expanded publication is only attached if its resolved jurisdiction matches the anchor publication jurisdiction for that dataset family.

### Gate 3 — contract gate

The resulting bridge output must still satisfy warehouse identity contracts, including:

- one row = one `family_id x publication_number`
- no unexpected publication-to-multi-family collision
- no null governed business keys

If these conditions fail, the expansion path must be treated as invalid until corrected.

---

## Why this policy exists

This policy exists because OPS family expansion can produce publication universes that overlap across different dataset families.

That overlap is useful as a discovery signal, but unsafe as direct warehouse identity truth.

Without explicit boundary control, the warehouse can incorrectly attach the same publication to multiple dataset families, breaking:

- family traceability
- search-serving trust
- BM25 reconciliation
- governance reporting
- reviewer confidence

---

## Implementation guidance

### Silver layer

`silver.ops_family_members` may retain raw source columns for auditability, but should also produce normalized publication identifiers suitable for governed downstream use.

### Gold layer

`gold.bridge_family_publication` must:

- preserve anchor rows
- treat OPS expansion as candidate-only
- apply normalization before publication attachment
- apply explicit boundary gating before accepting expanded publications

### dbt / testing layer

dbt tests are required as contract enforcement, but dbt is not the policy itself.

Policy defines the rule.  
SQL implements the rule.  
dbt verifies the rule.

At minimum, the bridge should be protected by:

- singular family collision test
- uniqueness on `(family_id, publication_number)`
- not-null checks on business keys
- format / normalization checks for governed publication identifiers

---

## Current implementation note

The current conservative boundary gate is intentionally strict.

It may reduce expansion coverage compared with unrestricted OPS-family full expansion.

This is acceptable because governed identity correctness takes priority over uncontrolled expansion volume.

Coverage can be expanded later only through additional explicit rules, not by removing boundary controls.

---

## Non-goals

This policy does not claim that OPS family data is wrong.

It only states that OPS family expansion must not be treated as identical to the warehouse’s canonical dataset family definition.

This policy also does not treat dbt failures as the primary control mechanism.

dbt is the verification layer, not the identity-definition layer.

---

## Summary rule

> Normalize first.  
> Bound expansion second.  
> Verify by contract tests third.