# Source of Truth Manifest v1

Status: Canonical  
Owner: Repo owner / governance owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This document defines the documentation authority order for this repository.

It exists to answer the following questions clearly:

- which documents are canonical
- which documents are explanatory only
- which documents are historical
- which documents may still be useful but must not guide new implementation
- how to resolve conflicts between files
- which files should be treated as current truth by humans and AI assistants

This manifest is the repository-level authority map for governed documentation.

---

## 2. Scope

This manifest applies to:

- `docs/`
- `policies/`
- architecture contracts
- governance policies
- truth-correction notes
- handover notes
- checklists
- benchmark notes
- incident notes
- archived material
- README-style navigation files

This manifest does not define naming rules.
Naming is governed by:

- `docs/architecture/naming_contract_v2.md`

This manifest does not define documentation class behavior in detail.
Documentation governance is defined by:

- `policies/documentation/documentation_governance_policy_v1.md`

---

## 3. Core principle

Not all files have equal authority.

A file may be:

- current and governing
- current but explanatory
- historically useful
- operationally helpful
- explicitly superseded
- archived only

A newer file does not automatically outrank an older file.

Authority depends on:

- file class
- status
- scope
- explicit supersession
- recognition by this manifest

---

## 4. Repository authority order

When documents conflict, use the following precedence order.

### 4.1 Highest authority

1. canonical policies under `policies/`
2. canonical contracts under `docs/architecture/`
3. this manifest and related authority documents under `docs/authority/`

### 4.2 Conditional authority

4. truth-correction notes that are explicitly recognized here or by a canonical policy/contract
5. current architecture explanations that do not conflict with higher-order canonical files

### 4.3 Lower authority

6. handover notes
7. checklists
8. benchmark notes
9. incident notes

### 4.4 Historical authority only

10. archived material
11. superseded documents
12. stale README guidance that conflicts with canonical files

---

## 5. Canonical document classes in this repo

The following document classes may act as current governing truth when marked canonical.

### 5.1 Canonical policies

Location:

- `policies/`

Examples:

- lifecycle policy
- retention policy
- backup and restore policy
- materialization policy
- serving release policy
- documentation governance policy
- platform boundary policy

Canonical policies define rules, gates, and operating discipline.

### 5.2 Canonical contracts

Location:

- `docs/architecture/`

Examples:

- naming contract
- source contracts
- identity contracts
- IPC/CPC contract
- retrieval layer contract

Canonical contracts define system boundaries, naming, data contracts, and stable design assumptions.

### 5.3 Canonical authority documents

Location:

- `docs/authority/`

Examples:

- source of truth manifest
- future precedence matrix
- canonical document inventory

Authority documents define how truth itself is ordered.

---

## 6. Non-canonical but useful document classes

The following classes are useful, but do not override canonical files by default.

### 6.1 Handover notes

Purpose:

- transfer working context
- summarize recent project state
- guide the next maintainer

Authority:

- informative
- may describe current reality
- does not override canonical policy or contract unless later absorbed into canonical documentation

### 6.2 Checklists

Purpose:

- execution guidance
- near-term sequencing
- practical work order

Authority:

- operational only
- not canonical unless promoted into policy or contract

### 6.3 Benchmark / memo / correction notes

Purpose:

- record performance evidence
- correct stale assumptions
- preserve milestone decisions

Authority:

- conditional
- may influence current truth if explicitly recognized by this manifest or a canonical document

### 6.4 Incident notes

Purpose:

- preserve failure evidence
- record root cause and corrective action

Authority:

- evidentiary
- not default governing truth

---

## 7. Recognition rule for truth-correction notes

A truth-correction note may temporarily influence current understanding only if at least one of the following is true:

1. it is explicitly referenced by this manifest
2. it is explicitly incorporated into a canonical contract or policy
3. it records a correction to a stale numeric or architectural statement that has not yet been updated elsewhere
4. its scope is narrow and clearly identified

Truth-correction notes should eventually be either:

- absorbed into canonical documentation, or
- marked historical

They should not remain permanent floating authority.

---

## 8. README rule

`README.md` files may guide navigation and onboarding.

They are allowed to:

- summarize folder purpose
- point to canonical documents
- help contributors navigate the repo

They are not allowed to:

- silently replace canonical rules
- contradict canonical policy or contract
- become the only location where key governance decisions exist

If `README.md` conflicts with a canonical file, the canonical file wins.

---

## 9. Superseded and archived material

### 9.1 Superseded files

A superseded file may remain in the repo for traceability, but it must not act as current truth.

A superseded file should:

- be marked `Superseded`, or
- be moved to archive, or
- both

It should also identify the replacement file.

### 9.2 Archived files

Archived files are historical only.

They may still be useful for:

- traceability
- incident context
- portfolio evidence
- understanding why a newer design exists

They must not be cited as current guidance unless explicitly reactivated.

---

## 10. Current repository authority map

This section records how this repo should currently be interpreted.

### 10.1 Current top-level canonical truth

Treat these as current governing sources when present and marked canonical:

- `docs/architecture/naming_contract_v2.md`
- `policies/documentation/documentation_governance_policy_v1.md`
- `policies/platform/platform_boundary_and_operating_model_v1.md`
- `policies/lifecycle/lifecycle_policy_v1.md`
- `policies/lifecycle/retention_policy_v1.md`
- `policies/lifecycle/materialization_policy_v1.md`
- `policies/lifecycle/backup_restore_policy_v1.md`
- `policies/lifecycle/serving_release_policy_v1.md`
- canonical architecture contracts such as IPC/CPC and source contracts

### 10.2 Current explanatory but non-governing sources

Treat these as useful but non-canonical unless promoted:

- handover notes
- operational checklists
- benchmark memos
- implementation diaries
- one-off migration notes

### 10.3 Current historical or archive-like sources

Treat these as historical by default:

- archived docs
- superseded contracts
- stale checklist variants
- stale benchmark comparisons
- outdated incident follow-ups that were later resolved

---

## 11. Conflict resolution rule

When two files appear to disagree, resolve conflict in this order:

### Step 1
Check whether one file is canonical and the other is not.

If yes, the canonical file wins.

### Step 2
If both are canonical, prefer the file whose scope is more specific and more directly relevant.

Example:
- a serving release policy outranks a generic note about "it worked once"

### Step 3
If a truth-correction note exists, check whether it is explicitly recognized by this manifest or already absorbed into a canonical file.

If yes, apply it.
If not, treat it as informative only.

### Step 4
If conflict still remains, create or update a canonical file instead of letting ambiguity persist.

---

## 12. Guidance for AI assistants and future maintainers

When using repository documentation to guide implementation:

1. read canonical policies first
2. read canonical contracts second
3. use this manifest to resolve ambiguity
4. treat handover and incident notes as secondary evidence
5. do not assume a benchmark note is a governing rule
6. do not assume a README is the highest authority
7. if a file looks important but lacks clear status, treat it cautiously until verified

### 12.1 Rule for AI systems

AI assistants should prefer:

- canonical policy
- canonical contract
- authority documents

before using:

- handovers
- checklists
- incidents
- old benchmark notes

---

## 13. Maintenance rule

This manifest must be updated when any of the following happens:

- a new canonical policy is created
- a new canonical contract supersedes an old one
- a truth-correction note must be recognized temporarily
- a major architecture document is archived or replaced
- a documentation class or folder responsibility changes

This file should be reviewed at:

- major governance milestones
- pre-demo cleanup
- handover preparation
- major repo structure changes

---

## 14. Immediate repository decisions

The following decisions are now adopted:

1. canonical policies outrank all non-canonical operational notes
2. canonical contracts outrank handovers, checklists, and incidents
3. this manifest is the repository-level truth-ordering reference
4. README files are navigation aids, not silent authority replacements
5. truth-correction notes may matter, but only when explicitly recognized
6. archived and superseded files remain for history, not for default implementation guidance
7. AI assistants should use this manifest to avoid documentation drift

---

## 15. Final principle

A governed repository should not force contributors to guess which file is real.

This manifest exists so that both humans and AI systems can answer:

- what is current
- what is historical
- what is governing
- what is only informative
- what should no longer drive implementation

If that cannot be answered quickly, the repository is not governed clearly enough.