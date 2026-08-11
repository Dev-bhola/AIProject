import google.generativeai as genai
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Configure the Gemini API once globally
genai.configure(api_key=settings.GEMINI_API_KEY)

def embed(text: str) -> list[float]:
    """Generates an embedding for a single string using Gemini API."""
    if not text.strip():
        return [0.0] * settings.EMBEDDING_DIMENSION
        
    try:
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Failed to generate Gemini embedding: {e}")
        # Return a zero vector so the pipeline doesn't crash completely,
        # but this will ruin retrieval for this chunk.
        return [0.0] * settings.EMBEDDING_DIMENSION

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a batch of strings using Gemini API."""
    if not texts:
        return []
        
    try:
        # Gemini natively supports lists of strings for batching
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=texts,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Failed to generate Gemini batch embeddings: {e}")
        return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
