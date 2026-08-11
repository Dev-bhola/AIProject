from fastapi import APIRouter, HTTPException
import backend.app.retrieval.search as search_module
from pydantic import BaseModel
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

class DocumentInfo(BaseModel):
    doc_id: str
    source_file: str

@router.get("/documents", response_model=list[DocumentInfo])
def get_documents():
    """
    Returns a unique list of available documents from the corpus.
    """
    search_module.load_bm25()
    corpus = search_module.BM25_CORPUS
    
    unique_docs = {}
    for chunk in corpus:
        doc_id = chunk.get("doc_id")
        source_file = chunk.get("source_file")
        if doc_id and source_file and doc_id not in unique_docs:
            unique_docs[doc_id] = source_file
            
    # Sort alphabetically by source_file
    sorted_docs = sorted(
        [DocumentInfo(doc_id=doc_id, source_file=source_file) for doc_id, source_file in unique_docs.items()],
        key=lambda x: x.source_file.lower()
    )
    
    return sorted_docs

@router.get("/documents/{doc_id}/pdf", response_class=FileResponse)
def get_document_pdf(doc_id: str):
    """
    Returns the raw PDF file for a given document ID, if it exists.
    """
    search_module.load_bm25()
    corpus = search_module.BM25_CORPUS
    
    source_file = None
    for chunk in corpus:
        if chunk.get("doc_id") == doc_id:
            source_file = chunk.get("source_file")
            break
            
    if not source_file:
        raise HTTPException(status_code=404, detail="Document not found in corpus.")
        
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        raise HTTPException(status_code=500, detail="Raw data directory not configured.")
        
    matches = list(raw_dir.rglob(source_file))
    if not matches:
        raise HTTPException(status_code=404, detail="PDF file not found on server.")
        
    pdf_path = matches[0]
    
    if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
        raise HTTPException(status_code=404, detail="Requested file is not a valid PDF.")
        
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=source_file,
        content_disposition_type="inline"
    )
