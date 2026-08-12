import requests
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Lazy loaded local embedder for when ENVIRONMENT == "local"
_local_embedding_model = None

def _get_local_model():
    global _local_embedding_model
    if _local_embedding_model is None:
        logger.info("Initializing fastembed locally for queries (ENVIRONMENT=local)...")
        try:
            from fastembed import TextEmbedding
            # Use the default model (BAAI/bge-small-en-v1.5) or explicitly set to match settings
            _local_embedding_model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
        except ImportError:
            logger.error("fastembed not installed. Cannot run local embeddings.")
            raise
    return _local_embedding_model

def get_hf_headers():
    if not settings.HF_API_KEY:
        logger.warning("HF_API_KEY is missing! Hugging Face embeddings will fail.")
        return {}
    return {"Authorization": f"Bearer {settings.HF_API_KEY}"}

def embed(text: str) -> list[float]:
    """Generates an embedding for a single string."""
    if not text.strip():
        return [0.0] * settings.EMBEDDING_DIMENSION
        
    if settings.ENVIRONMENT == "local":
        try:
            model = _get_local_model()
            # embed() returns an Iterable, we convert to Iterator and take the first
            return list(next(iter(model.embed([text]))))
        except Exception as e:
            logger.error(f"Failed to generate local embedding: {e}")
            return [0.0] * settings.EMBEDDING_DIMENSION

    # Production logic: Hugging Face Inference API
    api_url = f"https://router.huggingface.co/hf-inference/models/{settings.EMBEDDING_MODEL}/pipeline/feature-extraction"
    try:
        response = requests.post(api_url, headers=get_hf_headers(), json={"inputs": text}, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], list):
                return result[0]
            return result
        return [0.0] * settings.EMBEDDING_DIMENSION
    except Exception as e:
        logger.error(f"Failed to generate HF embedding: {e}")
        return [0.0] * settings.EMBEDDING_DIMENSION

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a batch of strings."""
    if not texts:
        return []
        
    if settings.ENVIRONMENT == "local":
        try:
            model = _get_local_model()
            return [list(arr) for arr in model.embed(texts)]
        except Exception as e:
            logger.error(f"Failed to generate local batch embeddings: {e}")
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
            
    # Production logic: Hugging Face Inference API
    api_url = f"https://router.huggingface.co/hf-inference/models/{settings.EMBEDDING_MODEL}/pipeline/feature-extraction"
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
