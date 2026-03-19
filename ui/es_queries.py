from elasticsearch import Elasticsearch
import pandas as pd

ES = Elasticsearch("http://localhost:9200")


def build_filter(state: dict) -> dict:
    must = []
    must_not = []

    if state.get("family_id"):
        must.append({"term": {"family_id": state["family_id"]}})

    if state.get("publication"):
        must.append({"term": {"rep_publication": state["publication"]}})

    if state.get("applicants"):
        must.append({"terms": {"applicants": state["applicants"]}})

    if state.get("inventor"):
        must.append({
            "wildcard": {
                "inventors": f"*{state['inventor']}*"
            }
        })

    if state.get("date_from") or state.get("date_to"):
        range_query = {}
        if state.get("date_from"):
            range_query["gte"] = state["date_from"]
        if state.get("date_to"):
            range_query["lte"] = state["date_to"]

        must.append({
            "range": {"publication_date": range_query}
        })

    return {
        "bool": {
            "must": must,
            "must_not": must_not
        }
    }


def agg_jurisdiction(filter_query: dict) -> pd.DataFrame:
    q = {
        "size": 0,
        "query": filter_query,
        "aggs": {
            "jur": {
                "terms": {
                    "field": "jurisdiction",
                    "size": 20
                }
            }
        }
    }

    res = ES.search(index="families_v1", body=q)
    buckets = res["aggregations"]["jur"]["buckets"]

    df = pd.DataFrame(buckets)
    df = df[df["key"] != "WO"]  # WO 不上圖

    return df.rename(columns={"key": "jurisdiction", "doc_count": "count"})


def agg_top_applicants(filter_query: dict) -> pd.DataFrame:
    q = {
        "size": 0,
        "query": filter_query,
        "aggs": {
            "apps": {
                "terms": {
                    "field": "applicants",
                    "size": 10
                }
            }
        }
    }

    res = ES.search(index="families_v1", body=q)
    buckets = res["aggregations"]["apps"]["buckets"]

    df = pd.DataFrame(buckets)

    return df.rename(columns={"key": "applicant", "doc_count": "count"})
