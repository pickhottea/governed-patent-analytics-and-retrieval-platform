# Semantic Pipeline — Execution Entrypoint

Status: Canonical  
Scope: Semantic Track A (Embedding Comparison)  
Data Source: Google canonical lane only  

This document defines how to execute the semantic pipeline end-to-end
under governed and reproducible conditions.

---

# 0. Preconditions

Required documents:

- policies/semantic/semantic_chunk_policy_v2_0.md
- policies/semantic/semantic_embedding_layer_policy_v2_0.md
- policies/semantic/claim_presence_policy_v2_0.md
- docs/architecture/semantic_station_contract.md
- docs/experiments/track_a_execution.md

Required environment:

- Python environment activated
- Chroma vector store available
- Deterministic run_id

---

# 1. Station 1 — Acquisition

Script:
scripts/canonical/step_b_google_acquisition.py

Output:
artifacts/_pipeline_runs/<RUN_ID>/02_text/google_raw/


Validation:
- family_id present
- has_claim_1 flag present
- governance_flags logged

---

# 2. Station 2 — Canonical Validation

Script:
scripts/canonical/step_c_validate_google_text.py


Output:
- google_text_validation_report.json
- google_language_distribution.json

Gate:
- missing_claim_1 <= threshold

---

# 3. Station 3 — Chunking

Script:
scripts/canonical/step_e_chunk_v2.py

Output:
artifacts/_pipeline_runs/<RUN_ID>/chunks_v2/

- claim_1.jsonl
- claim_set.jsonl
- spec.jsonl


Gate:
- Family IDs identical across files
- Exactly 3 chunks per family

---

# 4. Station 4 — Embedding

Script:
scripts/canonical/run_track_a_retrieval_v2.py


Models:
- patentsberta
- bge-m3

Output:
experiments/semantic_trackA_en95_v2/outputs/chroma/<model>/


Plus:
- embedding_manifest_v2.json
- SUCCESS.flag

---

# 5. Station 5 — Retrieval

Input:
- query_set_v2.jsonl

Output:
- results_<model>.jsonl
- top3_scoring.jsonl

All scoring must collapse to family level.

---

# 6. Station 6 — Evaluation

Manual + scripted evaluation:

Outputs:
- docs/experiments/embedding_comparison_consolidated.md
- docs/experiments/track_b_gpt_reasoning_stability_report.md

---

# Execution Order

Acquisition  
→ Validation  
→ Chunking  
→ Embedding  
→ Retrieval  
→ Evaluation  

No station may be skipped.

---

# Determinism Rule

A valid run must:

- Use fixed dataset
- Use fixed query set
- Log run_id
- Store embedding manifest
- Pass all gates

If any gate fails:
Pipeline is invalid.

---

# Archive Rule

All experimental or deprecated scripts must be placed in:
scripts/deprecated_archive/


Only scripts under:
scripts/canonical/


are production-valid.

---

# Final Principle

Policies define rules.  
Station contract defines boundaries.  
This file defines execution.

Together, they form a governed semantic pipeline.

