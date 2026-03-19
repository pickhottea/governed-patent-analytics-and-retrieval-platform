from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX_NAME = "patent_bm25_v1"

client = Elasticsearch(ES_URL)

mapping = {
    "settings": {
        "index": {
            "similarity": {
                "bm25_tuned": {
                    "type": "BM25",
                    "k1": 1.2,
                    "b": 0.75
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "family_id": {"type": "keyword"},
            "publication_number": {"type": "keyword"},
            "bm25_text": {
                "type": "text",
                "similarity": "bm25_tuned"
            }
        }
    }
}

if client.indices.exists(index=INDEX_NAME):
    client.indices.delete(index=INDEX_NAME)

client.indices.create(index=INDEX_NAME, body=mapping)
print(f"[DONE] created index: {INDEX_NAME}")