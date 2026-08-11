from fastapi import APIRouter, HTTPException
import logging
from backend.app.models.schemas import QueryRequest
from backend.app.retrieval.search import hybrid_search
from backend.app.generation.qa import generate_answer
from backend.app.utils.citations import deduplicate_sources

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/query")
def query_system(request: QueryRequest):
    try:
        search_result = hybrid_search(request.query, top_k=5)
        retrieved_chunks = search_result.results
        
        if not retrieved_chunks:
            return {
                "answer": "I could not find the answer in the provided legal sources.",
                "grounded": True,
                "citations": [],
                "sources": [],
                "sources_used": search_result.sources_used
            }
            
        gen_result = generate_answer(request.query, retrieved_chunks)
                
        return {
            "answer": gen_result["answer"],
            "grounded": gen_result["grounded"],
            "citations": gen_result["citations"],
            "sources": gen_result["citations"], # Backward compatibility for frontend
            "sources_used": search_result.sources_used
        }
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your request. Please try again.")
