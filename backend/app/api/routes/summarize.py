from fastapi import APIRouter, HTTPException
from backend.app.generation.summarizer import summarize_document
from backend.app.core.config import settings

router = APIRouter()

@router.get("/summarize/{doc_id}")
def summarize_doc(doc_id: str):
    try:
        summary = summarize_document(doc_id, settings.PARSED_DIR)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
