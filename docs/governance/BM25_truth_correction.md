# BM25 Truth Correction

## Purpose

This note replaces outdated wording that still says:

- BM25 searchable publication universe = 149
- `gold.bm25_document = 149`
- the missing case is still unresolved

That wording should now be treated as outdated.

---

## Current working truth

### Landscape lane
- family headline truth = **150**
- expanded members = **826**
- `gold.bridge_family_publication` total = **976**

### Current selected corpus
- current working selected corpus = **150**
- the serving-lane gap has been sealed in the current dbt working path
- `test_serving_lane_gap` now passes

---

## Important interpretation

The current selected corpus should be treated as:

- a **family-anchored selected-publication corpus**
- implemented operationally with representative `publication_number` keys
- not equivalent to the full expanded family-publication universe

This means the important distinction is:

- **family headline / selected representative corpus**
- versus
- **expanded family-publication footprint**

The important distinction is **not** a permanent 150 vs 149 mismatch.

---

## Confirmed repair status

The previously missing case `WO2021220141A1` was confirmed missing from `stg_rawdata_patents` even though it existed in `stg_raw_pub_to_family_id_v2`.

The working repair path now includes:
- `stg_rawdata_patents_backfill_gap`
- `stg_rawdata_patents_effective`

And the guardrail now includes:
- `test_serving_lane_gap`

So the issue should now be treated as:
- historically real
- technically addressed in the current working path
- no longer acceptable as an unresolved known gap

---

## What should now be considered stale

Any handover / memo / checklist text that still says one of the following should be treated as stale and replaceable:

- “BM25 searchable publication universe = 149”
- “`gold.bm25_document = 149`”
- “known missing case: `78373363 / WO2021220141A1`” as unresolved current status
- “do not collapse landscape family truth = 150 into BM25 publication truth = 149”

Those phrases described an earlier gap-analysis stage and should not remain as current truth.

---

## Replacement wording

Use wording like this instead:

> Current landscape truth supports 150 governed families with 826 expanded members and 976 family-publication bridge rows. The currently selected serving corpus is restored to 150 and should be treated as a family-anchored selected-publication corpus, not as an unresolved 149-publication mismatch. The important distinction is between selected family-anchored representative rows and the expanded family-publication footprint.

---

## Safe rule going forward

Keep these distinctions:

- do not mix **family headline reporting** with **expanded publication footprint**
- do not reopen canonical keys without need
- do not reopen the fixed family-expansion bridge path
- do not allow the serving-lane gap to return silently

But do **not** keep repeating the old 149 statement as if it were still current truth.

---

## One-line current truth

This project currently has:
- 150-family governed landscape truth
- a restored 150-row family-anchored selected corpus
- an expanded family-publication universe kept separate for footprint analysis
