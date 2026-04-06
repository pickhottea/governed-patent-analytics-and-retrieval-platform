# Retrieval Trace, Metrics, and Evidence Asset Design

## Purpose

This document defines the minimum evidence assets required for a governed patent retrieval platform.

The goal is not only to expose a search UI, but to continuously capture:
- benchmark queries
- reviewer judgments
- query execution trace
- retrieval result trace
- RAG review outcomes
- index refresh evidence
- retrieval and governance metrics

These assets support:
- retrieval evaluation
- human-in-the-loop review
- auditability
- lifecycle policy
- retention policy
- future semantic / hybrid / RAG extension

## Core Files

### queries_group1.csv
Benchmark query asset for retrieval evaluation.

Schema:
- query_id
- query_group
- query_type
- noise_level
- adversarial
- eval_layer
- query_text

### judgments.csv
Human-in-the-loop relevance judgment dataset.

Schema:
- ts_utc
- query_id
- query_group
- retrieval_system
- publication_number
- family_id
- rank_position
- score
- label
- reviewer
- notes

Allowed labels:
- highly_relevant
- somewhat_relevant
- irrelevant

### rag_review.csv
RAG answer review evidence log.

Schema:
- ts_utc
- question_id
- query_group
- retrieval_system
- question
- answer_text
- citations
- answer_supported
- citation_correct
- missing_evidence
- unsafe_overclaim
- reviewer
- notes

### query_run_log.csv
Query execution trace log.

Schema:
- ts_utc
- run_id
- query_id
- query_group
- query_text
- retrieval_system
- top_k
- latency_ms
- result_count
- index_name

### retrieval_result_log.csv
Exact result trace per query run.

Schema:
- ts_utc
- run_id
- query_id
- retrieval_system
- rank_position
- publication_number
- family_id
- score

### index_refresh_log.csv
Retrieval index lifecycle and refresh trace.

Schema:
- ts_utc
- index_name
- source_table
- document_count
- refresh_type
- run_status
- notes

## Trace Page Design

The Trace page should show per-run evidence with at least these fields:

| Field | Meaning |
|---|---|
| run_id | unique ID for each query execution |
| query_id | linked benchmark query |
| retrieval_system | bm25 / semantic / hybrid |
| top_k | requested number of returned hits |
| latency_ms | retrieval latency |
| returned_publications | publication list returned in that run |
| reviewer_actions | whether results were judged |
| linked_rag_reviews | whether the run was later used in RAG review |

Recommended implementation:
- read query_run_log.csv
- join retrieval_result_log.csv
- derive reviewer_actions from judgments.csv
- derive linked_rag_reviews from rag_review.csv

## Metrics to Collect

### Retrieval metrics
Required first-pass metrics:
- Precision@5
- nDCG@10

Optional later:
- Recall@10
- MRR

### Query-type metrics
Metrics should also be grouped by:
- STRUCTURAL
- FUNCTIONAL
- CAUSAL
- NOISE
- REVERSAL

### Governance and review metrics
Recommended:
- judgment_coverage
- reviewer_disagreement_rate
- rag_support_rate
- citation_correctness_rate
- unsafe_overclaim_rate

### Operational metrics
Recommended:
- query_latency_ms
- result_count
- index_document_count
- last_refresh_time

## Why These Assets Matter

These files are the minimum evidence backbone for:
- governed retrieval evaluation
- human reviewer workflow
- reproducible error analysis
- retrieval-to-answer traceability
- retention and lifecycle design

Without them, the platform is only a search demo.

## Retention Guidance

### Long-term retain
- queries_group1.csv
- judgments.csv
- rag_review.csv

### Medium-term retain
- query_run_log.csv
- retrieval_result_log.csv
- index_refresh_log.csv

### Short-term retain later-generated temp assets
Examples:
- pooled candidate dumps
- temporary experiment files
- transient intermediate outputs

Retention principle:
Retention follows function, not patent term.

## Recommended Next Step for Streamlit

The Streamlit app should next be upgraded so that:
1. search execution writes query_run_log.csv
2. returned hits write retrieval_result_log.csv
3. judgments write judgments.csv
4. trace page renders joined trace evidence
5. eval page computes Precision@5 and nDCG@10 from judgments
6. RAG review page writes rag_review.csv
