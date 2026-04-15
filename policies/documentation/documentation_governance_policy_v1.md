# Documentation Governance Policy v1

Status: Canonical  
Owner: Repo owner / governance owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This policy defines how documentation is governed in this repository.

It exists to prevent four common failures:

1. multiple files claiming to be the current truth
2. architecture notes being mistaken for enforceable policy
3. outdated handover or incident notes continuing to guide implementation
4. uncontrolled file growth without authority, ownership, or review discipline

This policy applies to all repository documentation and governance artifacts.

---

## 2. Scope

This policy governs:

- `docs/`
- `policies/`
- repository-level `README.md`
- architecture contracts
- handover notes
- incident notes
- benchmark notes
- truth-correction notes
- authority manifests
- governance runbooks
- policy documents

This policy does not govern:

- source code style
- warehouse object naming
- dbt model logic
- search index mappings
- runtime execution logic

Those are governed by their own contracts or engineering rules.

---

## 3. Documentation principles

All repository documentation must support at least one of these functions:

- explain
- govern
- record
- hand over
- evidence
- archive

If a file does not clearly serve one of these roles, it should not exist as a first-class document.

Documentation must be:

- understandable
- attributable
- reviewable
- non-contradictory
- clearly scoped
- clearly current or clearly historical

---

## 4. Folder responsibility model

### 4.1 `docs/`

`docs/` is for descriptive and explanatory material.

Typical contents:

- architecture contracts
- design explanations
- diagrams
- handover notes
- incident records
- benchmark notes
- examples
- source references
- authority manifests

`docs/` explains, records, and provides evidence.

### 4.2 `policies/`

`policies/` is for normative and governing material.

Typical contents:

- lifecycle rules
- retention rules
- documentation rules
- platform boundary rules
- materialization rules
- serving release rules
- semantic execution rules
- backup / restore rules
- archival / deprecation rules

`policies/` constrains, gates, and governs.

### 4.3 `docs/authority/`

`docs/authority/` is reserved for truth-ordering and repository authority documents.

Typical contents:

- source-of-truth manifest
- precedence matrix
- canonical document inventory
- superseded document registry

This folder helps humans and AI systems determine which documents are authoritative.

### 4.4 `docs/incidents/`

`docs/incidents/` stores incident records and investigation notes.

These files are historical evidence, not default governing truth.

### 4.5 `docs/archive/` and `policies/archive/`

Archive folders contain retained historical material.

Archived files may be useful for traceability, but they must not be treated as current governing instructions.

---

## 5. Documentation classes

All files governed by this policy fall into one of the following classes.

### 5.1 Contract

Defines architecture boundaries, data contracts, naming rules, or system responsibilities.

Examples:

- naming contract
- source contract
- identity contract
- IPC/CPC contract

Contracts may live in `docs/architecture/` when they describe system boundaries.

### 5.2 Policy

Defines mandatory rules, decision gates, or lifecycle expectations.

Examples:

- retention policy
- lifecycle policy
- documentation governance policy
- platform boundary policy

Policies must live in `policies/`.

### 5.3 Handover note

Transfers working knowledge between maintainers.

A handover note may describe reality, but it does not override canonical policy or contract.

### 5.4 Incident record

Records a failure, investigation, exception, or correction path.

Incident records are evidence, not primary governing truth.

### 5.5 Benchmark / memo / truth-correction note

Captures a dated benchmark, correction, or decision memo.

These files may influence current truth, but only if they are explicitly recognized by a canonical authority document.

### 5.6 Archive

Historical material retained for traceability only.

---

## 6. Required document metadata

Canonical and governance-relevant files should begin with a short metadata block.

Required fields for canonical files:

- `Status`
- `Owner`
- `Supersedes` or `Superseded by`
- `Last reviewed`

Recommended fields for important working files:

- `Status`
- `Owner`
- `Last reviewed`

### Allowed status values

- `Canonical`
- `Working`
- `Draft`
- `Archived`
- `Superseded`

### Meaning

- `Canonical` = current governing truth
- `Working` = active but not yet authoritative
- `Draft` = incomplete and not enforceable
- `Archived` = historical only
- `Superseded` = replaced by newer guidance

---

## 7. Audience model

Documentation in this repo is written for multiple audiences.

### 7.1 Primary audiences

- repo owner
- future maintainers
- contributors
- reviewers
- data platform builders
- retrieval / search builders
- dashboard builders

### 7.2 Secondary audiences

- interviewers
- collaborators
- external technical reviewers
- future AI assistants operating on this repo

### 7.3 Writing rule by audience

A file must be understandable by its intended audience without requiring hidden tribal knowledge.

If a file assumes repo-specific background, it must either:

- link the required contract or policy, or
- be downgraded from canonical status

---

## 8. Authority model

Not all documents have equal authority.

### 8.1 Authority order

When documents conflict, precedence is:

1. canonical policy
2. canonical contract
3. source-of-truth manifest or authority registry
4. truth-correction memo explicitly recognized by authority docs
5. current architecture explanation
6. handover note
7. checklist
8. incident note
9. archive material

### 8.2 Important rule

A newer file does not automatically outrank an older file.

Authority comes from:

- document class
- status
- scope
- explicit supersession
- recognition by repository authority documents

### 8.3 README rule

`README.md` may guide navigation, but it must not silently override canonical contracts or policies.

If README guidance conflicts with a canonical contract or policy, the canonical contract or policy wins.

---

## 9. Change control

### 9.1 Who may create canonical files

Canonical files should be created only by:

- repo owner
- architecture owner
- governance owner
- explicitly delegated maintainer

### 9.2 Who may modify canonical files

Canonical files may be modified only when the change includes:

- reason for change
- scope of impact
- affected files or systems
- supersession rule if applicable
- review confirmation by owner or delegate

### 9.3 Who may create working notes

Any contributor may create:

- working notes
- handover notes
- incident records
- benchmark notes

But these files must not present themselves as canonical unless explicitly approved.

---

## 10. Canonicalization rule

A file becomes canonical only when all are true:

1. its purpose is clear
2. its owner is named
3. its scope is stated
4. its status is marked `Canonical`
5. it does not conflict with higher-authority current truth
6. it is placed in the correct folder
7. it is either referenced by an authority manifest or clearly discoverable as the current governing file

If these are not true, the file is not canonical even if its content is useful.

---

## 11. Superseded and archive rules

### 11.1 Superseded rule

When a file is replaced:

- mark it `Superseded`, or
- move it to archive, or
- both

It must also identify the replacement file.

### 11.2 Archive rule

A file may be archived when:

- it is historical
- it is no longer the current truth
- it is retained for traceability
- it still has explanatory or incident value

### 11.3 No silent drift

A stale file must not remain in a live folder without either:

- active review and confirmation, or
- explicit superseded / archived marking

---

## 12. Documentation review cadence

Canonical documents should be reviewed:

- when system boundaries change
- when a new serving lane is introduced
- when a view is replaced by a table
- when a policy is added or retired
- when architecture ownership changes
- at major project milestones
- before handover
- before public demo or portfolio presentation

Recommended minimum cadence for canonical files:

- once per milestone, or
- once per quarter

---

## 13. Relationship to naming contract

This policy works with the naming contract.

The naming contract decides:

- how files should be named
- version and date suffix standards
- README exception rules
- folder naming conventions

This policy decides:

- what kind of document a file is
- where it should live
- how authoritative it is
- who may modify it
- how conflicts are resolved

---

## 14. Relationship to lifecycle and retention

This policy does not define storage retention durations directly.

However, it does define when documentation should move between states such as:

- active
- working
- superseded
- archived

Retention and lifecycle timing should be handled by:

- `policies/lifecycle/lifecycle_policy_v1.md`
- `policies/lifecycle/retention_policy_v1.md`

---

## 15. Immediate repository decisions

The following decisions are now adopted:

1. `docs/` and `policies/` remain separate by responsibility
2. canonical governance rules must live under `policies/`
3. descriptive architecture and evidence may live under `docs/`
4. archive material must not continue acting as current truth
5. handover and incident notes do not override canonical policy by default
6. a source-of-truth manifest should be maintained under `docs/authority/`
7. canonical documents must have visible ownership and status metadata

---

## 16. Enforcement guidance

If a contributor is unsure where a file belongs, apply this test:

### Put it in `docs/` if it mainly:
- explains
- records
- hands over
- demonstrates
- benchmarks
- documents an incident

### Put it in `policies/` if it mainly:
- requires
- forbids
- gates
- defines lifecycle
- defines authority
- defines release conditions
- defines retention or deprecation rules

If a file tries to do both, split it.

---

## 17. Final principle

Documentation is part of the governed system.

A good document must make clear:

- what it is
- who it is for
- whether it governs or explains
- whether it is current or historical
- who is allowed to change it
- what happens if it conflicts with another file

If those things are not obvious, the file is not governed well enough.