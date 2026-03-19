# Governed Patent Analytics and Retrieval Platform

SQL-first patent warehouse and retrieval platform built with SQL Server, dbt, Elasticsearch, and Power BI-facing marts.

## Overview

This repository demonstrates a governed data platform for patent analytics and retrieval.

The platform is designed around three goals:

1. Build a reliable SQL Server warehouse for patent data using bronze, silver, and gold layers.
2. Model analytics-ready datasets in dbt for reporting and downstream BI use.
3. Validate a retrieval-serving path using Elasticsearch BM25 over publication-level patent text.

This project is intentionally platform-oriented rather than notebook-oriented. The emphasis is on warehouse structure, data contracts, governed modeling, testability, and reproducible serving flows.

## Platform Scope

Current platform scope includes:

- SQL Server warehouse foundation
- bronze / silver / gold warehouse modeling
- dbt staging and marts
- applicant, inventor, IPC, and publication analytics models
- Power BI-facing marts
- Elasticsearch BM25 serving validation
- architecture contracts and governance policies

## Architecture Summary

The platform is organized into two connected layers:

### 1. Analytics warehouse layer
This layer supports reporting, dimensional modeling, and BI consumption.

Core characteristics:

- SQL Server as warehouse engine
- layered modeling with bronze, silver, and gold
- dbt for staging, marts, and tests
- publication, family, IPC, applicant, and inventor analytics
- Power BI-facing marts for dashboard consumption

### 2. Retrieval serving layer
This layer supports publication-level search serving.

Core characteristics:

- BM25-oriented document preparation
- Elasticsearch index create / load / query flow
- publication-level retrieval validation
- governed distinction between analytics truth and serving corpus

## Repository Structure

```text
.
├── artifacts/
│   └── audit/
├── dbt_patent_led/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── dbt_project.yml
│   └── packages.yml
├── docs/
│   └── architecture/
├── policies/
├── scripts/
│   └── ingest/
├── search/
│   └── elasticsearch/
├── sql/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── archive/
├── tests/
├── ui/
├── .gitignore
└── PIPELINE_ENTRYPOINT.md

## Key Components

### SQL warehouse

The `sql/` directory contains the warehouse SQL used to define and load the bronze, silver, and gold layers.

Examples include:

- raw patent ingestion structures
- family expansion logic
- IPC bridges and dimensions
- applicant and inventor facts
- BM25 preparation tables

### dbt project

The `dbt_patent_led/` directory contains dbt models for:

- staging models over warehouse sources
- analytics marts
- applicant / inventor facts
- IPC and publication dimensions
- Power BI-facing marts
- dbt tests for integrity and modeling confidence

### Elasticsearch serving

The `search/elasticsearch/` directory contains the serving validation flow:

- create index
- load BM25 documents
- query and inspect retrieval results

## Current Modeling Decisions

### Canonical keys

The current platform keeps these keys fixed:

- `family_id` as the canonical family key
- `publication_number` as the canonical publication key

These keys should not be replaced casually, because they are part of the architecture and traceability contracts.

### Family-publication alignment

A critical modeling correction was made so that family expansion is attached through family-level OPS mapping rather than seed-publication exact matching.

This means the valid path is:

`family_id -> bridge_family_ops_cluster -> ops_family_members`

and not the older broken rule based on direct seed-publication matching.

### Publication dimension semantics

`dim_publication` is treated as publication-only, not as a strict family-publication uniqueness contract. This is important because publication-family relationships may reflect broader family interpretation behavior and should not be oversimplified.

## Data Quality and Testing

This platform uses both SQL validation checks and dbt tests.

Current test coverage includes:

- `unique`
- `not_null`
- `accepted_values`
- `relationships`

Representative tested entities include:

- family OPS bridge
- family-publication bridge
- publication IPC bridge
- BM25 document publication key
- applicant fact keys
- inventor fact keys

## Power BI-Facing Marts

The current dbt project includes marts designed for BI-facing consumption, including:

- family publication coverage
- IPC distribution
- applicant organization
- inventor
- BM25 publication metadata

These marts are intended to provide cleaner reporting surfaces than pointing BI tools directly at lower-level bridge or fact tables.

## Elasticsearch Validation

The retrieval-serving flow has been validated end to end:

- index creation
- BM25 document load
- query execution

This confirms that the platform is not only an analytics warehouse, but also supports a governed retrieval-serving path.

## Governance Positioning

This repository is meant to show platform and governance thinking, not only model building.

The project emphasizes:

- controlled warehouse layers
- architecture contracts
- naming and traceability discipline
- governed distinction between analytics truth and retrieval serving
- reproducible modeling and validation steps

## Tech Stack

- SQL Server
- T-SQL
- dbt
- Elasticsearch
- Python
- Power BI

## What This Repository Demonstrates

This repository is intended as a portfolio-grade example of:

- analytics engineering
- data platform design
- warehouse modeling
- governed semantic / retrieval architecture
- SQL-first implementation discipline
- BI-facing mart design
- search-serving validation

## Status

Current status:

- warehouse foundation established
- dbt marts and tests implemented
- Power BI-facing marts created
- Elasticsearch BM25 serving validated
- architecture and governance documentation organized

## Next Possible Extensions

Potential future extensions include:

- expanding README-level execution instructions
- adding dbt docs generation and model documentation
- adding Power BI screenshots or dashboard documentation
- integrating more explicit release/run metadata
- further narrowing or modularizing ingestion and serving scripts

## Author

Built by pickhottea as a governed patent analytics and retrieval platform project focused on data governance, warehouse design, analytics engineering, and retrieval-serving architecture.
