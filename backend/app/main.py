import os
import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.retrieval.search import get_qdrant_client

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from backend.app.retrieval.search import load_bm25

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_bm25()
    
    version_path = os.path.join("data", "corpus_version.json")
    bm25_version = None
    if not os.path.exists(version_path):
        logger.warning("corpus_version.json not found — cannot verify index consistency. Run ingestion to generate it.")
    else:
        with open(version_path, 'r', encoding='utf-8') as f:
            bm25_version = json.load(f).get("corpus_version")
            
    qdrant_client = get_qdrant_client()
    qdrant_version = None
    if qdrant_client:
        try:
            points = qdrant_client.retrieve(collection_name=settings.QDRANT_COLLECTION_NAME, ids=[999999999])
            if points and points[0].payload:
                qdrant_version = points[0].payload.get("corpus_version")
            else:
                logger.warning("Qdrant sentinel point not found — cannot verify index consistency. Re-run ingestion to generate it.")
        except Exception as e:
            logger.warning(f"Failed to retrieve Qdrant sentinel point: {e}")
            
    if bm25_version and qdrant_version:
        if bm25_version != qdrant_version:
            logger.warning(f"BM25 and Qdrant may be out of sync — BM25 version: {bm25_version}, Qdrant version: {qdrant_version}")
        else:
            logger.info(f"Corpus consistency verified — version: {bm25_version}")

    yield

app = FastAPI(title="Legal RAG System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(api_router, prefix="/api")
