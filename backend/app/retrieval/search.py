import os
import pickle
import logging
from dataclasses import dataclass
from qdrant_client import QdrantClient
from backend.app.ingestion.embedder import embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HybridSearchResult:
    results: list[dict]
    sources_used: list[str]

from backend.app.core.config import settings

def get_qdrant_client():
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    if not url or not api_key:
        logger.warning("QDRANT_URL or QDRANT_API_KEY not set. Vector search will fail.")
        return None
    return QdrantClient(url=url, api_key=api_key)

def _vector_search_internal(query: str, top_k: int = 5) -> tuple[list[dict], bool]:
    client = get_qdrant_client()
    if not client:
        return [], False
        
    try:
        query_vector = embed(query)
        search_result = client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_vector,
            limit=top_k
        )
        results = []
        for hit in search_result.points:
            if hit.payload is not None:
                results.append(hit.payload)
        return results, True
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return [], False

def vector_search(query: str, top_k: int = 5) -> list[dict]:
    return _vector_search_internal(query, top_k)[0]

BM25_INDEX = None
BM25_CORPUS = None

def load_bm25():
    global BM25_INDEX, BM25_CORPUS
    if BM25_INDEX is not None and BM25_CORPUS is not None:
        return
        
    data_dir = os.path.join("data")
    index_path = os.path.join(data_dir, "bm25_index.pkl")
    corpus_path = os.path.join(data_dir, "bm25_corpus.pkl")
    
    if not os.path.exists(index_path) or not os.path.exists(corpus_path):
        raise RuntimeError("BM25 index or corpus not found. Please run the ingestion pipeline first.")
        
    with open(index_path, 'rb') as f:
        BM25_INDEX = pickle.load(f)
    with open(corpus_path, 'rb') as f:
        BM25_CORPUS = pickle.load(f)

def _keyword_search_internal(query: str, top_k: int = 5) -> tuple[list[dict], bool]:
    try:
        load_bm25()
        if BM25_INDEX is None or BM25_CORPUS is None:
            raise ValueError("BM25 not loaded")
        import re
        tokenized_query = re.findall(r'\w+', query.lower())
        doc_scores = BM25_INDEX.get_scores(tokenized_query)
        
        top_n_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_n_indices:
            if doc_scores[idx] > 0:
                results.append(BM25_CORPUS[idx])
                
        return results, True
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return [], False

def keyword_search(query: str, top_k: int = 5) -> list[dict]:
    return _keyword_search_internal(query, top_k)[0]

def hybrid_search(query: str, top_k: int = 5) -> HybridSearchResult:
    vector_results, vector_success = _vector_search_internal(query, top_k=top_k * 4)
    keyword_results, keyword_success = _keyword_search_internal(query, top_k=top_k * 4)
    
    sources_used = []
    if vector_success: sources_used.append("vector")
    if keyword_success: sources_used.append("keyword")
    
    rrf_k = settings.RRF_K
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
    
    final_results = []
    seen_pages = {}
    for doc_id in sorted_doc_ids:
        doc = doc_map[doc_id]
        page_key = (doc.get("source_file"), doc.get("page_number"))
        seen_pages[page_key] = seen_pages.get(page_key, 0) + 1
        
        # Diversity: cap at 2 chunks per page
        if seen_pages[page_key] > 2:
            continue
            
        final_results.append(doc)
        if len(final_results) >= top_k:
            break
            
    return HybridSearchResult(results=final_results, sources_used=sources_used)

if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv(dotenv_path=os.path.join("backend", ".env"))
    
    test_query = "What is the objective of Milestone 1?"
    print(f"Testing Hybrid Search with query: '{test_query}'")
    
    results = hybrid_search(test_query, top_k=3)
    
    print(f"\nTop {len(results.results)} Results (sources: {results.sources_used}):")
    for i, res in enumerate(results.results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Source: {res.get('source_file')} (Page {res.get('page_number')})")
        text_out = res.get('text', '').encode('utf-8', 'ignore').decode('utf-8')
        print(f"Text: {text_out[:200]}...")
