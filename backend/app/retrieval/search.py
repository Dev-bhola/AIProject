import os
import pickle
import logging
from qdrant_client import QdrantClient
from backend.app.ingestion.embedder import embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_qdrant_client():
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    if not url or not api_key:
        logger.warning("QDRANT_URL or QDRANT_API_KEY not set. Vector search will fail.")
        return None
    return QdrantClient(url=url, api_key=api_key)

def vector_search(query: str, top_k: int = 5) -> list[dict]:
    client = get_qdrant_client()
    if not client:
        return []
        
    try:
        query_vector = embed(query)
        search_result = client.query_points(
            collection_name="legal_chunks",
            query=query_vector,
            limit=top_k
        )
        results = []
        for hit in search_result.points:
            if hit.payload is not None:
                results.append(hit.payload)
        return results
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []

def keyword_search(query: str, top_k: int = 5) -> list[dict]:
    data_dir = os.path.join("data")
    index_path = os.path.join(data_dir, "bm25_index.pkl")
    corpus_path = os.path.join(data_dir, "bm25_corpus.pkl")
    
    if not os.path.exists(index_path) or not os.path.exists(corpus_path):
        logger.warning("BM25 index or corpus not found. Keyword search will return empty.")
        return []
        
    try:
        with open(index_path, 'rb') as f:
            bm25 = pickle.load(f)
        with open(corpus_path, 'rb') as f:
            corpus = pickle.load(f)
            
        tokenized_query = query.lower().split(" ")
        doc_scores = bm25.get_scores(tokenized_query)
        
        top_n_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_n_indices:
            if doc_scores[idx] > 0:
                results.append(corpus[idx])
                
        return results
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return []

def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    vector_results = vector_search(query, top_k=top_k * 2)
    keyword_results = keyword_search(query, top_k=top_k * 2)
    
    rrf_k = 60
    rrf_scores = {}
    
    for rank, doc in enumerate(vector_results):
        doc_id = doc.get("chunk_id")
        if doc_id:
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            
    for rank, doc in enumerate(keyword_results):
        doc_id = doc.get("chunk_id")
        if doc_id:
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            
    doc_map = {doc.get("chunk_id"): doc for doc in vector_results + keyword_results if doc.get("chunk_id")}
    
    sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    
    final_results = [doc_map[doc_id] for doc_id in sorted_doc_ids[:top_k]]
    return final_results

if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv(dotenv_path=os.path.join("backend", ".env"))
    
    test_query = "What is the objective of Milestone 1?"
    print(f"Testing Hybrid Search with query: '{test_query}'")
    
    results = hybrid_search(test_query, top_k=3)
    
    print(f"\nTop {len(results)} Results:")
    for i, res in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Source: {res.get('source_file')} (Page {res.get('page_number')})")
        text_out = res.get('text', '').encode('utf-8', 'ignore').decode('utf-8')
        print(f"Text: {text_out[:200]}...")
