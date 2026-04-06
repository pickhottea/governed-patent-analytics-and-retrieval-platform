# Retrieval Layer — BM25

## Overview

The retrieval layer is implemented using Elasticsearch with a BM25 ranking model. It serves as the primary entry point for text-based search over the patent corpus.

## Architecture

SQL Server (gold.bm25_document)
        ↓
Elasticsearch index (patent_bm25_v1)
        ↓
BM25 ranking (_search API)


## Corpus Definition

- Source: `gold.bm25_document`
- Grain: 1 row = 1 publication
- Total: 150 publications

## Key Principle

> Search universe is defined by governed identity (anchor), not by artifact availability.

This ensures:

- Full coverage of selected publications
- No data loss due to missing abstract artifacts
- Stable and predictable retrieval behavior

## Fallback Strategy

- If abstract exists → use title + abstract
- If abstract missing → use title only

This guarantees all publications are searchable.

## Index

- Name: `patent_bm25_v1`
- Engine: Elasticsearch 8.x
- Field: `bm25_text`

## Validation

- Indexed documents: 150
- Query tested: `"LED lighting system"`
- Result: ranked hits with valid BM25 scores

## Role in System

BM25 acts as:

- First-stage retrieval (recall layer)
- Input provider for semantic / RAG pipeline
- Search backend for UI (Streamlit)

It is not replaced by semantic search, but complemented by it.
