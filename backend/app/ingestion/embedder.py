import requests
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_hf_headers():
    if not settings.HF_API_KEY:
        logger.warning("HF_API_KEY is missing! Hugging Face embeddings will fail.")
        return {}
    return {"Authorization": f"Bearer {settings.HF_API_KEY}"}

def embed(text: str) -> list[float]:
    """Generates an embedding for a single string using Hugging Face Inference API."""
    if not text.strip():
        return [0.0] * settings.EMBEDDING_DIMENSION
        
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.EMBEDDING_MODEL}"
    
    try:
        response = requests.post(api_url, headers=get_hf_headers(), json={"inputs": text}, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        # Hugging Face feature extraction pipeline returns a list of floats
        # Sometimes it returns a nested list if batching, so we handle it
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], list):
                return result[0]
            return result
        return [0.0] * settings.EMBEDDING_DIMENSION
    except Exception as e:
        logger.error(f"Failed to generate HF embedding: {e}")
        return [0.0] * settings.EMBEDDING_DIMENSION

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a batch of strings using Hugging Face Inference API."""
    if not texts:
        return []
        
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.EMBEDDING_MODEL}"
    
    try:
        response = requests.post(api_url, headers=get_hf_headers(), json={"inputs": texts}, timeout=60)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            return result
        return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
    except Exception as e:
        logger.error(f"Failed to generate HF batch embeddings: {e}")
        return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
