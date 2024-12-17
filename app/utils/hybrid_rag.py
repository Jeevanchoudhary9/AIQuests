import os
from .. import es, embedding_model
import PyPDF2

index_name = os.getenv("DOC_INDEX_NAME")

def index_documents(documents, organisation_id):
    # Index each document with text, embedding, and organisation_id
    for doc in documents:
        embedding = embedding_model.encode(doc["text"]).tolist()  # Generate embedding
        es.index(index=index_name, id=doc["id"], document={
            "organisation_id": organisation_id,
            "text": doc["text"],
            "embedding": embedding
        })
        print(f"Document ID {doc['id']} indexed with organisation_id {organisation_id}.")


def reciprocal_rank_fusion(bm25_results, semantic_results, k=60):
    fused_scores = {}
    for doc_id, rank in bm25_results.items():
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (rank + k)
    for doc_id, rank in semantic_results.items():
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (rank + k)
    return fused_scores

def get_next_elasticsearch_id(index_name):
    query = {
        "size": 0,
        "aggs": {
            "max_id": {
                "max": {
                    "field": "id"
                }
            }
        }
    }
    try:
        response = es.search(index=index_name, body=query)
        max_id = int(response["aggregations"]["max_id"]["value"])
        return max_id + 1
    except:
        return 1  # Start from ID 1 if no documents exist
    
def pdf_to_documents(pdf_path, index_name, organisation_id):
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)
        print(f"PDF Loaded: {pdf_path} | Total Pages: {total_pages}")

        next_id = get_next_elasticsearch_id(index_name)
        documents = []

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:  # Skip pages with no text
                document = {
                    "id": next_id,
                    "text": text
                }
                documents.append(document)
                print(f"Prepared Document ID {next_id} for indexing.")
                next_id += 1

        # Pass organisation_id for indexing
        index_documents(documents, organisation_id)


def hybrid_search(query, organisation_id, top_k=5):
    # 1. Perform Syntactic Search (BM25) with organisation_id filter
    bm25_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"text": query}}
                ],
                "filter": [
                    {"term": {"organisation_id": organisation_id}}
                ]
            }
        }
    }
    bm25_response = es.search(index=index_name, body=bm25_query, size=top_k)
    bm25_results = {
        hit["_id"]: idx + 1 for idx, hit in enumerate(bm25_response["hits"]["hits"])
    }

    # 2. Perform Semantic Search (KNN) with organisation_id filter
    query_embedding = embedding_model.encode(query).tolist()
    semantic_query = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"organisation_id": organisation_id}}
                ]
            }
        },
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 50
        }
    }
    semantic_response = es.search(index=index_name, body=semantic_query, size=top_k)
    semantic_results = {
        hit["_id"]: idx + 1 for idx, hit in enumerate(semantic_response["hits"]["hits"])
    }

    # 3. Combine Results using RRF
    fused_results = reciprocal_rank_fusion(bm25_results, semantic_results)
    sorted_results = sorted(fused_results.items(), key=lambda x: x[1], reverse=True)

    return sorted_results