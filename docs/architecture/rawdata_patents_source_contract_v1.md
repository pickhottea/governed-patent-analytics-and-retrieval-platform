## Source name

`rawdata_patents.xlsx`

---

## Source purpose

This source provides the initial anchor dataset for the patent warehouse rebuild.

Its role is to provide:

- one selected publication per family
- the initial family anchor for warehouse loading
- the publication anchor for BM25 seed preparation
- descriptive metadata for landscape analysis

---

## Source classification

This source is classified as:

> selected-publication anchor source

It is **not** classified as:

- full publication universe
- full family-member source
- semantic authority source
- complete text source

---

## Grain

Source grain:

> 1 row = 1 selected publication representing 1 family

Observed current dataset behavior:

- total rows = 150
- distinct `publication_number` = 150
- distinct `family_id` = 150

For the current delivered file, selected publication and family are in 1:1 relation.

---

## Source authority

This source is authoritative for:

- dataset family anchor
- selected publication anchor
- title
- applicants text
- inventors text
- IPC text
- CPC display text
- key publication / priority dates

This source is **not** authoritative for:

- full family-member expansion
- semantic full text
- semantic chunking
- full claims coverage
- abstract completeness unless explicitly present and verified in a later version

---

## Current source columns

Observed columns:

- `No`
- `title`
- `inventors`
- `applicants`
- `publication_number`
- `grant_number`
- `earliest_priority_date`
- `ipc`
- `cpc`
- `publication_date`
- `earliest_publication`
- `family_id`

---

## Column handling rules

### Kept for contract
- `family_id`
- `publication_number`
- `grant_number`
- `title`
- `inventors`
- `applicants`
- `earliest_priority_date`
- `ipc`
- `cpc`
- `publication_date`
- `earliest_publication`

### Excluded from warehouse contract
- `No`

Reason:

`No` is only a worksheet sequence column and does not carry business identity.

---

## Identity interpretation

### Family identity
`family_id` is the family-level identifier for this dataset.

### Publication identity
`publication_number` is the selected publication identifier for this dataset.

### Important interpretation
This file does **not** imply that one family globally has only one publication.

It only means:

> for this dataset version, one selected publication was chosen to represent one family

---

## Use cases supported

This source may be used for:

- initial bronze loading
- family anchor creation
- selected publication creation
- landscape seed analysis
- BM25 seed preparation based on currently available anchor text

---

## Use cases not supported

This source must not be used alone for:

- family coverage analysis across all member publications
- jurisdiction spread across full family members
- grant/publication kind coverage across family members
- semantic authority text construction
- final chunk-level RAG serving

Those require additional raw sources.

---

## Relationship to other sources

This source must later be paired with at least one family-member expansion source, for example:

- OPS family member extraction output
- family-member JSONL export
- equivalent all-member publication source

Warehouse direction:

> selected-publication anchor source + family-member expansion source

Both are required for full coverage-oriented warehouse modeling.

---

## Data quality expectations for current file version

Expected current checks:

- `family_id` null count = 0
- `publication_number` null count = 0
- `family_id` distinct count = row count
- `publication_number` distinct count = row count

Current file-level expectation:

- rows = 150
- family count = 150
- publication count = 150

---

## Known limitations

Known current limitations include:

- no family-member expansion
- possible multi-valued IPC in one field
- possible multi-valued inventors in one field
- possible multi-valued applicants in one field
- possible Excel formatting artifacts in text fields
- no guarantee of normalized date formatting without ingestion handling
- no abstract column in current loaded contract version

---

## Contract decision

This source is accepted as:

> bronze selected-publication anchor input

It is not accepted as:

> full patent warehouse raw coverage source

Current implemented scope from this source includes bronze anchor loading and downstream IPC-path modeling.
