import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("backend", ".env"))

class Settings:
    QDRANT_URL = os.environ.get("QDRANT_URL")
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    PARSED_DIR = os.path.join("data", "parsed")

settings = Settings()
