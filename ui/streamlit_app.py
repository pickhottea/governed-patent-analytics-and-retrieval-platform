import os
import csv
import uuid
import math
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
import pyodbc
import streamlit as st
from elasticsearch import Elasticsearch


ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "patent_bm25_v1")

SQL_SERVER = os.getenv("SQL_SERVER", "127.0.0.1,1433")
SQL_DATABASE = os.getenv("SQL_DATABASE", "patent_analytics")
SQL_USERNAME = os.getenv("SQL_USERNAME", "sa")
SQL_PASSWORD = os.getenv("SQLSERVER_SA_PASSWORD", "")
SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")

QUERY_GROUP1_PATH = "artifacts/eval/queries_group1.csv"
QUERY_GROUP2_PATH = "artifacts/eval/queries_group2.csv"
JUDGMENT_PATH = "artifacts/eval/judgments.csv"
RAG_REVIEW_PATH = "artifacts/eval/rag_review.csv"

QUERY_RUN_LOG_PATH = "artifacts/audit/query_run_log.csv"
RETRIEVAL_RESULT_LOG_PATH = "artifacts/audit/retrieval_result_log.csv"
INDEX_REFRESH_LOG_PATH = "artifacts/audit/index_refresh_log.csv"

JUDGMENT_SCHEMA = [
    "ts_utc", "query_id", "query_group", "retrieval_system", "publication_number",
    "family_id", "rank_position", "score", "label", "reviewer", "notes"
]
RAG_REVIEW_SCHEMA = [
    "ts_utc", "question_id", "query_group", "retrieval_system", "question",
    "answer_text", "citations", "answer_supported", "citation_correct",
    "missing_evidence", "unsafe_overclaim", "reviewer", "notes"
]
QUERY_RUN_SCHEMA = [
    "ts_utc", "run_id", "query_id", "query_group", "query_text",
    "retrieval_system", "top_k", "latency_ms", "result_count", "index_name"
]
RETRIEVAL_RESULT_SCHEMA = [
    "ts_utc", "run_id", "query_id", "retrieval_system", "rank_position",
    "publication_number", "family_id", "score"
]
INDEX_REFRESH_SCHEMA = [
    "ts_utc", "index_name", "source_table", "document_count",
    "refresh_type", "run_status", "notes"
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_es_client() -> Elasticsearch:
    return Elasticsearch(ES_URL)


def get_sql_conn() -> pyodbc.Connection:
    if not SQL_PASSWORD:
        raise ValueError("Missing environment variable: SQLSERVER_SA_PASSWORD")

    conn_str = (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def ensure_columns(df: pd.DataFrame, required_cols: List[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=required_cols)
    df = df.copy()
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")
    return df[required_cols]


def ensure_csv(path: str, header: List[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not Path(path).exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)


def append_csv(path: str, row: List[str]) -> None:
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def load_csv(path: str) -> pd.DataFrame:
    if not Path(path).exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_csv_schema(path: str, schema: List[str]) -> pd.DataFrame:
    return ensure_columns(load_csv(path), schema)


def save_csv_schema(df: pd.DataFrame, path: str, schema: List[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    ensure_columns(df, schema).to_csv(path, index=False)


def ensure_all_files() -> None:
    ensure_csv(JUDGMENT_PATH, JUDGMENT_SCHEMA)
    ensure_csv(RAG_REVIEW_PATH, RAG_REVIEW_SCHEMA)
    ensure_csv(QUERY_RUN_LOG_PATH, QUERY_RUN_SCHEMA)
    ensure_csv(RETRIEVAL_RESULT_LOG_PATH, RETRIEVAL_RESULT_SCHEMA)
    ensure_csv(INDEX_REFRESH_LOG_PATH, INDEX_REFRESH_SCHEMA)


def load_queries() -> pd.DataFrame:
    frames = []
    for p in [QUERY_GROUP1_PATH, QUERY_GROUP2_PATH]:
        df = load_csv(p)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["query_id", "query_group", "query_type", "query_text"])
    out = pd.concat(frames, ignore_index=True)
    for col in ["query_id", "query_group", "query_type", "query_text"]:
        if col not in out.columns:
            out[col] = None
    return out


def resolve_query_by_id(query_id: str, queries_df: pd.DataFrame) -> Optional[dict]:
    if queries_df.empty:
        return None
    match = queries_df[queries_df["query_id"].astype(str) == str(query_id)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def bm25_search(query: str, size: int = 10) -> tuple[list[dict], int]:
    es = get_es_client()
    body = {
        "size": size,
        "query": {
            "match": {
                "bm25_text": query
            }
        }
    }
    start = time.perf_counter()
    resp = es.search(index=ES_INDEX, body=body)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return resp["hits"]["hits"], latency_ms


def get_index_document_count() -> int:
    try:
        return int(get_es_client().count(index=ES_INDEX)["count"])
    except Exception:
        return 0


def hydrate_publications(publication_numbers: List[str]) -> Dict[str, dict]:
    if not publication_numbers:
        return {}
    placeholders = ",".join(["?"] * len(publication_numbers))
    sql = f"""
    SELECT
        publication_number,
        family_id,
        title,
        abstract,
        bm25_text,
        retrieval_mode,
        loaded_at
    FROM gold.bm25_document
    WHERE publication_number IN ({placeholders})
    """
    with get_sql_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, publication_numbers)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]

    out: Dict[str, dict] = {}
    for row in rows:
        rec = dict(zip(cols, row))
        out[str(rec["publication_number"])] = rec
    return out


def log_query_run(
    run_id: str,
    query_id: str,
    query_group: str,
    query_text: str,
    retrieval_system: str,
    top_k: int,
    latency_ms: int,
    result_count: int,
    index_name: str,
) -> None:
    append_csv(
        QUERY_RUN_LOG_PATH,
        [
            utc_now_iso(), run_id, query_id, query_group, query_text,
            retrieval_system, str(top_k), str(latency_ms), str(result_count), index_name
        ],
    )


def log_retrieval_results(run_id: str, query_id: str, retrieval_system: str, hits: List[dict]) -> None:
    for rank_position, hit in enumerate(hits, start=1):
        src = hit.get("_source", {})
        append_csv(
            RETRIEVAL_RESULT_LOG_PATH,
            [
                utc_now_iso(),
                run_id,
                query_id,
                retrieval_system,
                str(rank_position),
                str(src.get("publication_number", "")),
                str(src.get("family_id", "")),
                str(hit.get("_score", "")),
            ],
        )


def toggle_judgment(
    query_id: str,
    query_group: str,
    retrieval_system: str,
    publication_number: str,
    family_id: str,
    rank_position: int,
    score: float,
    label: str,
    reviewer: str,
    notes: str,
) -> None:
    df = load_csv_schema(JUDGMENT_PATH, JUDGMENT_SCHEMA)

    mask = (
        (df["query_id"].astype(str) == str(query_id)) &
        (df["retrieval_system"].astype(str) == str(retrieval_system)) &
        (df["publication_number"].astype(str) == str(publication_number))
    )

    existing_label = None
    if mask.any():
        existing_rows = df[mask].copy()
        if not existing_rows.empty and "ts_utc" in existing_rows.columns:
            existing_rows = existing_rows.sort_values("ts_utc", ascending=False)
        existing_label = str(existing_rows.iloc[0]["label"])

    df = df[~mask].copy()

    if existing_label == label:
        save_csv_schema(df, JUDGMENT_PATH, JUDGMENT_SCHEMA)
        return

    new_row = pd.DataFrame([{
        "ts_utc": utc_now_iso(),
        "query_id": query_id,
        "query_group": query_group,
        "retrieval_system": retrieval_system,
        "publication_number": publication_number,
        "family_id": family_id,
        "rank_position": rank_position,
        "score": f"{score:.6f}",
        "label": label,
        "reviewer": reviewer,
        "notes": notes,
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_csv_schema(df, JUDGMENT_PATH, JUDGMENT_SCHEMA)


def get_existing_judgment_label(
    judgments_df: pd.DataFrame,
    query_id: str,
    retrieval_system: str,
    publication_number: str,
) -> Optional[str]:
    if judgments_df.empty:
        return None

    match = judgments_df[
        (judgments_df["query_id"].astype(str) == str(query_id)) &
        (judgments_df["retrieval_system"].astype(str) == str(retrieval_system)) &
        (judgments_df["publication_number"].astype(str) == str(publication_number))
    ]
    if match.empty:
        return None

    latest = match.sort_values("ts_utc", ascending=False).iloc[0]
    return str(latest["label"])


def render_label_badge(label: Optional[str]) -> None:
    if label == "highly_relevant":
        text = "Saved label: Highly Relevant"
        bg = "#d1fae5"
        fg = "#065f46"
    elif label == "somewhat_relevant":
        text = "Saved label: Somewhat Relevant"
        bg = "#fef3c7"
        fg = "#92400e"
    elif label == "irrelevant":
        text = "Saved label: Irrelevant"
        bg = "#fee2e2"
        fg = "#991b1b"
    else:
        text = "Saved label: Not labeled yet"
        bg = "#e5e7eb"
        fg = "#374151"

    st.markdown(
        f'<div style="display:inline-block;padding:6px 12px;border-radius:999px;background:{bg};color:{fg};font-weight:600;">{text}</div>',
        unsafe_allow_html=True,
    )


def append_rag_review(
    question_id: str,
    query_group: str,
    retrieval_system: str,
    question: str,
    answer_text: str,
    citations: str,
    answer_supported: str,
    citation_correct: str,
    missing_evidence: str,
    unsafe_overclaim: str,
    reviewer: str,
    notes: str,
) -> None:
    append_csv(
        RAG_REVIEW_PATH,
        [
            utc_now_iso(), question_id, query_group, retrieval_system, question,
            answer_text, citations, answer_supported, citation_correct,
            missing_evidence, unsafe_overclaim, reviewer, notes
        ],
    )


def shorten(text: str, max_len: int = 500) -> str:
    if text is None:
        return ""
    text = str(text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + " ..."


def label_gain(label: str) -> int:
    return 2 if label == "highly_relevant" else 1 if label == "somewhat_relevant" else 0


def compute_precision_at_k(results: List[str], judgments: pd.DataFrame, query_id: str, retrieval_system: str, k: int = 5) -> float:
    if judgments.empty:
        return 0.0

    rel = judgments[
        (judgments["query_id"].astype(str) == str(query_id)) &
        (judgments["retrieval_system"].astype(str) == str(retrieval_system))
    ].copy()
    if rel.empty:
        return 0.0

    rel["gain"] = rel["label"].map(label_gain)
    rel_map = dict(zip(rel["publication_number"].astype(str), rel["gain"]))
    topk = [str(x) for x in results[:k]]
    hits = sum(1 for pub in topk if rel_map.get(pub, 0) > 0)
    return hits / k if k > 0 else 0.0


def compute_dcg(labels: List[int]) -> float:
    return sum(gain / math.log2(i + 1) for i, gain in enumerate(labels, start=1))


def compute_ndcg_at_k(results: List[str], judgments: pd.DataFrame, query_id: str, retrieval_system: str, k: int = 10) -> float:
    if judgments.empty:
        return 0.0

    rel = judgments[
        (judgments["query_id"].astype(str) == str(query_id)) &
        (judgments["retrieval_system"].astype(str) == str(retrieval_system))
    ].copy()
    if rel.empty:
        return 0.0

    rel["gain"] = rel["label"].map(label_gain)
    rel_map = dict(zip(rel["publication_number"].astype(str), rel["gain"]))

    predicted = [rel_map.get(str(pub), 0) for pub in results[:k]]
    ideal = sorted(rel["gain"].tolist(), reverse=True)[:k]

    idcg = compute_dcg(ideal)
    if idcg == 0:
        return 0.0
    return compute_dcg(predicted) / idcg


def compute_judgment_coverage(queries_df: pd.DataFrame, judgments_df: pd.DataFrame) -> float:
    if queries_df.empty:
        return 0.0

    judged_query_ids = set(judgments_df["query_id"].dropna().astype(str).unique()) if not judgments_df.empty else set()
    total_ids = set(queries_df["query_id"].dropna().astype(str).unique())
    if not total_ids:
        return 0.0
    covered = sum(1 for q in total_ids if q in judged_query_ids)
    return covered / len(total_ids)


def compute_rag_support_rate(rag_df: pd.DataFrame) -> float:
    if rag_df.empty:
        return 0.0
    yes = (rag_df["answer_supported"].astype(str).str.lower() == "yes").sum()
    return yes / len(rag_df)


def compute_citation_correctness_rate(rag_df: pd.DataFrame) -> float:
    if rag_df.empty:
        return 0.0
    yes = (rag_df["citation_correct"].astype(str).str.lower() == "yes").sum()
    return yes / len(rag_df)


def compute_unsafe_overclaim_rate(rag_df: pd.DataFrame) -> float:
    if rag_df.empty:
        return 0.0
    yes = (rag_df["unsafe_overclaim"].astype(str).str.lower() == "yes").sum()
    return yes / len(rag_df)


def latest_refresh_time(refresh_df: pd.DataFrame) -> str:
    if refresh_df.empty or "ts_utc" not in refresh_df.columns:
        return "N/A"
    try:
        return str(refresh_df["ts_utc"].dropna().astype(str).iloc[-1])
    except Exception:
        return "N/A"


def build_trace_view(
    query_run_df: pd.DataFrame,
    result_df: pd.DataFrame,
    judgments_df: pd.DataFrame,
    rag_df: pd.DataFrame,
) -> pd.DataFrame:
    if query_run_df.empty:
        return pd.DataFrame()

    result_grouped = pd.DataFrame(columns=["run_id", "returned_publications"])
    if not result_df.empty:
        temp = result_df.copy()
        temp["publication_number"] = temp["publication_number"].astype(str)
        result_grouped = temp.groupby("run_id", as_index=False)["publication_number"].apply(
            lambda s: ", ".join(s.tolist())
        )
        result_grouped.columns = ["run_id", "returned_publications"]

    reviewer_actions = pd.DataFrame(columns=["run_id", "reviewer_actions"])
    if not result_df.empty and not judgments_df.empty:
        result_temp = result_df.copy()
        judgment_temp = judgments_df.copy()

        result_temp["publication_number"] = result_temp["publication_number"].astype(str)
        judgment_temp["publication_number"] = judgment_temp["publication_number"].astype(str)

        merged = result_temp.merge(
            judgment_temp,
            on=["query_id", "retrieval_system", "publication_number"],
            how="inner"
        )

        reviewer_actions = merged.groupby("run_id", as_index=False).size()
        reviewer_actions.columns = ["run_id", "reviewer_actions"]

    linked_rag_reviews = pd.DataFrame(columns=["question_id", "linked_rag_reviews"])
    if not rag_df.empty and "question_id" in rag_df.columns:
        linked_rag_reviews = rag_df.groupby("question_id", as_index=False).size()
        linked_rag_reviews.columns = ["question_id", "linked_rag_reviews"]

    trace = query_run_df.copy()
    trace = trace.merge(result_grouped, on="run_id", how="left")
    trace = trace.merge(reviewer_actions, on="run_id", how="left")
    trace = trace.merge(linked_rag_reviews, left_on="query_id", right_on="question_id", how="left")

    trace["reviewer_actions"] = trace["reviewer_actions"].fillna(0).astype(int)
    trace["linked_rag_reviews"] = trace["linked_rag_reviews"].fillna(0).astype(int)
    trace["returned_publications"] = trace["returned_publications"].fillna("")

    keep_cols = [
        "ts_utc", "run_id", "query_id", "query_group", "retrieval_system", "top_k",
        "latency_ms", "result_count", "index_name", "returned_publications",
        "reviewer_actions", "linked_rag_reviews"
    ]
    return trace[keep_cols].sort_values("ts_utc", ascending=False)

st.set_page_config(page_title="Patent Retrieval Platform", layout="wide")
st.title("Governed Patent Retrieval Platform")
st.caption("BM25 search, judgment capture, retrieval evaluation, trace evidence, and RAG review logging")

ensure_all_files()

queries_df = load_queries()
judgments_df = load_csv_schema(JUDGMENT_PATH, JUDGMENT_SCHEMA)
rag_reviews_df = load_csv_schema(RAG_REVIEW_PATH, RAG_REVIEW_SCHEMA)
query_run_df = load_csv_schema(QUERY_RUN_LOG_PATH, QUERY_RUN_SCHEMA)
retrieval_result_df = load_csv_schema(RETRIEVAL_RESULT_LOG_PATH, RETRIEVAL_RESULT_SCHEMA)
index_refresh_df = load_csv_schema(INDEX_REFRESH_LOG_PATH, INDEX_REFRESH_SCHEMA)

for key, value in {
    "last_hits": [],
    "last_run_id": None,
    "last_query_id": "MANUAL",
    "last_query_group": "manual",
    "last_query_text": "",
    "last_retrieval_system": "bm25",
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

with st.sidebar:
    st.header("Search Settings")

    query_mode = st.radio("Query Mode", ["Benchmark query", "Manual query"], index=0)

    selected_query_id = "MANUAL"
    selected_query_group = "manual"
    selected_query_text = ""

    if query_mode == "Benchmark query" and not queries_df.empty:
        query_options = queries_df["query_id"].dropna().astype(str).tolist()
        selected_query_id = st.selectbox("Query ID", query_options)
        selected = resolve_query_by_id(selected_query_id, queries_df)
        selected_query_group = str(selected.get("query_group", "unknown")) if selected else "unknown"
        selected_query_text = str(selected.get("query_text", "")) if selected else ""
        st.text_area("Benchmark Query", value=selected_query_text, height=180, disabled=True)
    else:
        selected_query_text = st.text_area("Manual Query", value="", height=180)

    retrieval_system = st.selectbox("Retrieval System", ["bm25"], index=0, disabled=True)
    reviewer_name = st.text_input("Reviewer", value="pickhottea")
    size = st.slider("Top K", min_value=5, max_value=30, value=10, step=5)
    run = st.button("Run Search", type="primary")

tabs = st.tabs(["BM25 Search", "Judge Results", "Retrieval Eval", "RAG Review", "Trace"])
tab_bm25, tab_judge, tab_eval, tab_rag, tab_trace = tabs

with tab_bm25:
    if run and selected_query_text.strip():
        with st.spinner("Searching Elasticsearch..."):
            hits, latency_ms = bm25_search(selected_query_text.strip(), size)

        run_id = str(uuid.uuid4())
        log_query_run(
            run_id=run_id,
            query_id=selected_query_id,
            query_group=selected_query_group,
            query_text=selected_query_text.strip(),
            retrieval_system=retrieval_system,
            top_k=size,
            latency_ms=latency_ms,
            result_count=len(hits),
            index_name=ES_INDEX,
        )
        log_retrieval_results(run_id, selected_query_id, retrieval_system, hits)

        st.session_state["last_hits"] = hits
        st.session_state["last_run_id"] = run_id
        st.session_state["last_query_id"] = selected_query_id
        st.session_state["last_query_group"] = selected_query_group
        st.session_state["last_query_text"] = selected_query_text.strip()
        st.session_state["last_retrieval_system"] = retrieval_system

        st.success(f"Returned {len(hits)} hits in {latency_ms} ms")

    hits = st.session_state["last_hits"]

    if hits:
        pub_nos = [h["_source"]["publication_number"] for h in hits]
        metadata = {}
        hydration_warning = None

        try:
            metadata = hydrate_publications(pub_nos)
        except Exception as e:
            hydration_warning = str(e)

        if hydration_warning:
            st.warning(f"SQL hydration skipped: {hydration_warning}")

        judgments_df = load_csv_schema(JUDGMENT_PATH, JUDGMENT_SCHEMA)

        for idx, hit in enumerate(hits, start=1):
            src = hit["_source"]
            pub = str(src["publication_number"])
            fam = str(src["family_id"])
            score = float(hit["_score"])
            meta = metadata.get(pub, {})

            title = meta.get("title") or pub
            abstract = meta.get("abstract")
            bm25_text = meta.get("bm25_text") or src.get("bm25_text", "")

            existing_label = get_existing_judgment_label(
                judgments_df,
                st.session_state["last_query_id"],
                st.session_state["last_retrieval_system"],
                pub,
            )

            with st.container(border=True):
                st.markdown(f"### {idx}. {title}")
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**publication_number**: `{pub}`")
                c2.write(f"**family_id**: `{fam}`")
                c3.write(f"**score**: `{score:.4f}`")

                st.write("**abstract**")
                st.write(shorten(abstract, 900) if abstract else "_NULL_")

                with st.expander("Show indexed text"):
                    st.text(shorten(bm25_text, 2500))

                st.write("**Judgment status**")
                render_label_badge(existing_label)

                st.write("**Judgment capture**")
                jc1, jc2, jc3, jc4 = st.columns([1, 1, 1, 2])
                notes = jc4.text_input(
                    "Notes",
                    key=f"judge_notes_{idx}",
                    placeholder="optional label note",
                    label_visibility="collapsed",
                )

                if jc1.button(
                    "Highly Relevant",
                    key=f"high_{idx}",
                    type="primary" if existing_label == "highly_relevant" else "secondary",
                ):
                    toggle_judgment(
                        query_id=st.session_state["last_query_id"],
                        query_group=st.session_state["last_query_group"],
                        retrieval_system=st.session_state["last_retrieval_system"],
                        publication_number=pub,
                        family_id=fam,
                        rank_position=idx,
                        score=score,
                        label="highly_relevant",
                        reviewer=reviewer_name,
                        notes=notes,
                    )
                    st.rerun()

                if jc2.button(
                    "Somewhat Relevant",
                    key=f"some_{idx}",
                    type="primary" if existing_label == "somewhat_relevant" else "secondary",
                ):
                    toggle_judgment(
                        query_id=st.session_state["last_query_id"],
                        query_group=st.session_state["last_query_group"],
                        retrieval_system=st.session_state["last_retrieval_system"],
                        publication_number=pub,
                        family_id=fam,
                        rank_position=idx,
                        score=score,
                        label="somewhat_relevant",
                        reviewer=reviewer_name,
                        notes=notes,
                    )
                    st.rerun()

                if jc3.button(
                    "Irrelevant",
                    key=f"irr_{idx}",
                    type="primary" if existing_label == "irrelevant" else "secondary",
                ):
                    toggle_judgment(
                        query_id=st.session_state["last_query_id"],
                        query_group=st.session_state["last_query_group"],
                        retrieval_system=st.session_state["last_retrieval_system"],
                        publication_number=pub,
                        family_id=fam,
                        rank_position=idx,
                        score=score,
                        label="irrelevant",
                        reviewer=reviewer_name,
                        notes=notes,
                    )
                    st.rerun()
    else:
        st.info("Run a query to capture results and judgments.")

with tab_judge:
    judgments_df = load_csv_schema(JUDGMENT_PATH, JUDGMENT_SCHEMA)
    st.subheader("Retrieval Judgment Dataset")
    if judgments_df.empty:
        st.info("No judgments yet.")
    else:
        st.dataframe(judgments_df, use_container_width=True)
        st.write(f"Rows: {len(judgments_df)}")

with tab_eval:
    judgments_df = load_csv_schema(JUDGMENT_PATH, JUDGMENT_SCHEMA)
    queries_df = load_queries()
    query_run_df = load_csv_schema(QUERY_RUN_LOG_PATH, QUERY_RUN_SCHEMA)
    rag_reviews_df = load_csv_schema(RAG_REVIEW_PATH, RAG_REVIEW_SCHEMA)
    index_refresh_df = load_csv_schema(INDEX_REFRESH_LOG_PATH, INDEX_REFRESH_SCHEMA)

    st.subheader("Retrieval Evaluation")
    if queries_df.empty:
        st.info("No benchmark queries found.")
    else:
        selected_eval_query_id = st.selectbox(
            "Evaluation Query ID",
            queries_df["query_id"].dropna().astype(str).tolist()
        )
        selected_eval_row = resolve_query_by_id(selected_eval_query_id, queries_df)

        if selected_eval_row:
            st.write(f"**query_type**: {selected_eval_row.get('query_type', 'N/A')}")
            st.write(selected_eval_row.get("query_text", ""))

        topk_eval = st.slider("Eval Top K", min_value=3, max_value=20, value=10, step=1)

        if st.button("Run Eval for Selected Query"):
            eval_query_text = str(selected_eval_row.get("query_text", "")) if selected_eval_row else ""
            hits, _ = bm25_search(eval_query_text, size=topk_eval)
            pubs = [h["_source"]["publication_number"] for h in hits]

            p_at_5 = compute_precision_at_k(pubs, judgments_df, selected_eval_query_id, "bm25", k=min(5, topk_eval))
            ndcg_at_10 = compute_ndcg_at_k(pubs, judgments_df, selected_eval_query_id, "bm25", k=min(10, topk_eval))

            m1, m2 = st.columns(2)
            m1.metric("Precision@5", f"{p_at_5:.3f}")
            m2.metric("nDCG@10", f"{ndcg_at_10:.3f}")

            st.write("Returned publications")
            st.write(pubs)

        st.markdown("### Governance and operational metrics")
        index_doc_count = get_index_document_count()
        judgment_coverage = compute_judgment_coverage(queries_df, judgments_df)
        rag_support_rate = compute_rag_support_rate(rag_reviews_df)
        citation_correctness_rate = compute_citation_correctness_rate(rag_reviews_df)
        unsafe_overclaim_rate = compute_unsafe_overclaim_rate(rag_reviews_df)

        avg_latency = 0.0
        if not query_run_df.empty and "latency_ms" in query_run_df.columns:
            avg_latency = pd.to_numeric(query_run_df["latency_ms"], errors="coerce").fillna(0).mean()

        g1, g2, g3 = st.columns(3)
        g1.metric("Judgment Coverage", f"{judgment_coverage:.1%}")
        g2.metric("RAG Support Rate", f"{rag_support_rate:.1%}")
        g3.metric("Citation Correctness", f"{citation_correctness_rate:.1%}")

        g4, g5, g6 = st.columns(3)
        g4.metric("Unsafe Overclaim Rate", f"{unsafe_overclaim_rate:.1%}")
        g5.metric("Average Query Latency (ms)", f"{avg_latency:.1f}")
        g6.metric("Index Document Count", str(index_doc_count))

        st.write(f"**Last refresh time**: {latest_refresh_time(index_refresh_df)}")

with tab_rag:
    st.subheader("RAG Answer Review Dataset")

    default_question_id = st.session_state["last_query_id"] if st.session_state["last_query_id"] else "MANUAL"
    default_query_group = st.session_state["last_query_group"] if st.session_state["last_query_group"] else "manual"

    question_id = st.text_input("Question ID", value=str(default_question_id))
    question = st.text_area("Question", value=st.session_state["last_query_text"] or "", height=120)
    answer = st.text_area("Draft answer", value="", height=220)
    citations = st.text_input("Citations", value="", placeholder="e.g. WO2021236966A1; EP4215802A1")

    c1, c2 = st.columns(2)
    supported = c1.selectbox("Answer supported?", ["yes", "partially", "no"])
    citation_correct = c2.selectbox("Citation correct?", ["yes", "partially", "no"])

    c3, c4 = st.columns(2)
    missing_evidence = c3.selectbox("Missing important evidence?", ["yes", "no"])
    unsafe_overclaim = c4.selectbox("Unsafe overclaim?", ["yes", "no"])

    rag_notes = st.text_area("Review notes", value="", height=120)

    if st.button("Log RAG Review"):
        append_rag_review(
            question_id,
            default_query_group,
            st.session_state["last_retrieval_system"],
            question,
            answer,
            citations,
            supported,
            citation_correct,
            missing_evidence,
            unsafe_overclaim,
            reviewer_name,
            rag_notes,
        )
        st.success("RAG review logged.")

    rag_reviews_df = load_csv_schema(RAG_REVIEW_PATH, RAG_REVIEW_SCHEMA)
    if not rag_reviews_df.empty:
        st.dataframe(rag_reviews_df, use_container_width=True)

with tab_trace:
    query_run_df = load_csv_schema(QUERY_RUN_LOG_PATH, QUERY_RUN_SCHEMA)
    retrieval_result_df = load_csv_schema(RETRIEVAL_RESULT_LOG_PATH, RETRIEVAL_RESULT_SCHEMA)
    judgments_df = load_csv_schema(JUDGMENT_PATH, JUDGMENT_SCHEMA)
    rag_reviews_df = load_csv_schema(RAG_REVIEW_PATH, RAG_REVIEW_SCHEMA)

    trace_df = build_trace_view(query_run_df, retrieval_result_df, judgments_df, rag_reviews_df)

    st.subheader("Trace Evidence")
    if trace_df.empty:
        st.info("No trace runs yet.")
    else:
        st.dataframe(trace_df, use_container_width=True)
        st.markdown("### Trace fields")
        st.markdown(
            """
- `run_id`: unique ID for each query execution  
- `query_id`: linked benchmark query  
- `retrieval_system`: bm25 / semantic / hybrid  
- `top_k`: requested number of hits  
- `latency_ms`: retrieval latency  
- `returned_publications`: publication list returned in that run  
- `reviewer_actions`: count of linked judgments  
- `linked_rag_reviews`: count of linked RAG reviews  
            """
        )
