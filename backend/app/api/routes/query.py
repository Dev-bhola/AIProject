from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import QueryRequest
from backend.app.retrieval.search import hybrid_search
from backend.app.generation.qa import generate_answer
from backend.app.utils.citations import deduplicate_sources

router = APIRouter()

@router.post("/query")
def query_system(request: QueryRequest):
    try:
        retrieved_chunks = hybrid_search(request.query, top_k=5)
        
        if not retrieved_chunks:
            return {
                "answer": "I cannot answer this based on the provided documents.",
                "sources": []
            }
            
        answer = generate_answer(request.query, retrieved_chunks)
        sources = deduplicate_sources(retrieved_chunks)
                
        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
