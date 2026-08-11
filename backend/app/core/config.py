import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("backend", ".env"))

class Settings:
    QDRANT_URL = os.environ.get("QDRANT_URL")
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    PARSED_DIR = os.path.join("data", "parsed")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    QDRANT_COLLECTION_NAME = "legal_chunks"
    CHUNK_SIZE = 900
    CHUNK_OVERLAP = 150
    RRF_K = 60
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

settings = Settings()
