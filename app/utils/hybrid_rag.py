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
    

def pdf_to_documents(pdf_path, organisation_id):
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


def hybrid_search(query, organisation_id, top_k=3, score_threshold=0.5):
    # 1. BM25 Search
    bm25_query = {
        "query": {
            "bool": {
                "must": [{"match": {"text": query}}],
                "filter": [{"term": {"organisation_id": organisation_id}}]
            }
        }
    }
    bm25_response = es.search(index=index_name, body=bm25_query, size=top_k)
    bm25_results = {
        hit["_id"]: hit["_score"] for hit in bm25_response["hits"]["hits"]
    }

    # 2. Semantic Search
    query_embedding = embedding_model.encode(query).tolist()
    semantic_query = {
        "query": {"bool": {"filter": [{"term": {"organisation_id": organisation_id}}]}},
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 50
        }
    }
    semantic_response = es.search(index=index_name, body=semantic_query, size=top_k)
    semantic_results = {
        hit["_id"]: hit["_score"] for hit in semantic_response["hits"]["hits"]
    }

    # Combine Scores
    fused_scores = reciprocal_rank_fusion(bm25_results, semantic_results)
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

    # Filter low-score results
    result_texts = []
    for doc_id, score in sorted_results:
        if score >= score_threshold:  # Only include relevant results
            doc = es.get(index=index_name, id=doc_id, _source_includes=["text"])
            result_texts.append(doc["_source"]["text"])

    return " ".join(result_texts) if result_texts else ""  # Return combined context or empty