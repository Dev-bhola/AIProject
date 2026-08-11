from fastapi import APIRouter
from backend.app.api.routes import query, summarize, documents, golden_set

api_router = APIRouter()

api_router.include_router(query.router, tags=["query"])
api_router.include_router(summarize.router, tags=["summarize"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(golden_set.router, tags=["golden_set"])
