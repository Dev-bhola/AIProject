from fastapi import APIRouter
from backend.app.api.routes import query, summarize

api_router = APIRouter()

api_router.include_router(query.router, tags=["query"])
api_router.include_router(summarize.router, tags=["summarize"])
