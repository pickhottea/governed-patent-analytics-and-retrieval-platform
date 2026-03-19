from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX_NAME = "patent_bm25_v1"

client = Elasticsearch(ES_URL)

query_text = "LED light apparatus"

resp = client.search(
    index=INDEX_NAME,
    size=10,
    query={
        "match": {
            "bm25_text": query_text
        }
    }
)

hits = resp["hits"]["hits"]

print(f"total hits: {resp['hits']['total']}")
for i, hit in enumerate(hits, start=1):
    src = hit["_source"]
    print("-" * 80)
    print(f"rank: {i}")
    print(f"score: {hit['_score']}")
    print(f"doc_id: {src.get('doc_id')}")
    print(f"family_id: {src.get('family_id')}")
    print(f"publication_number: {src.get('publication_number')}")
    print(f"text preview: {src.get('bm25_text', '')[:200]}")