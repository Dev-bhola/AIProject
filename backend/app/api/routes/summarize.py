from fastapi import APIRouter, HTTPException
import logging
from backend.app.generation.summarizer import summarize_document
from backend.app.models.schemas import SummaryResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/summarize/{doc_id}", response_model=SummaryResponse)
async def summarize_doc(doc_id: str):
    try:
        summary = await summarize_document(doc_id)
        return summary
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Summarization failed for doc {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your request. Please try again.")
    except Exception as e:
        logger.error(f"Summarization failed for doc {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your request. Please try again.")
