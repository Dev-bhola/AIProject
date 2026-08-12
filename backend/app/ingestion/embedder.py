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

def _mean_pool(token_vectors: list[list[float]]) -> list[float]:
    """Average per-token vectors into a single sentence vector, for the rare case
    the API returns unpooled token-level output instead of a pre-pooled vector."""
    dim = len(token_vectors[0])
    sums = [0.0] * dim
    for vec in token_vectors:
        for i, v in enumerate(vec):
            sums[i] += v
    count = len(token_vectors)
    return [s / count for s in sums]

def _extract_single_vector(result) -> list[float]:
    if not isinstance(result, list) or len(result) == 0:
        raise ValueError(f"Unexpected HF feature-extraction response shape: {type(result)}")
    if isinstance(result[0], list):
        return _mean_pool(result)
    return result

HF_EMBED_URL_TEMPLATE = "https://router.huggingface.co/hf-inference/models/{model}/pipeline/feature-extraction"

def embed(text: str) -> list[float]:
    """Generates an embedding for a single string.

    Raises on failure rather than returning a zero-vector: a silent zero-vector
    looks like a successful embedding to every caller and poisons vector search
    results without any visible signal. Callers (search.py's _vector_search_internal)
    already catch failures here and gracefully degrade to keyword-only search.
    """
    if not text.strip():
        return [0.0] * settings.EMBEDDING_DIMENSION

    if settings.ENVIRONMENT == "local":
        model = _get_local_model()
        # embed() returns an Iterable, we convert to Iterator and take the first
        return list(next(iter(model.embed([text]))))

    # Production logic: Hugging Face Inference API
    api_url = HF_EMBED_URL_TEMPLATE.format(model=settings.EMBEDDING_MODEL)
    response = requests.post(api_url, headers=get_hf_headers(), json={"inputs": text}, timeout=20)
    response.raise_for_status()
    return _extract_single_vector(response.json())

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a batch of strings. Raises on failure — see embed()."""
    if not texts:
        return []

    if settings.ENVIRONMENT == "local":
        model = _get_local_model()
        return [list(arr) for arr in model.embed(texts)]

    # Production logic: Hugging Face Inference API
    api_url = HF_EMBED_URL_TEMPLATE.format(model=settings.EMBEDDING_MODEL)
    response = requests.post(api_url, headers=get_hf_headers(), json={"inputs": texts}, timeout=60)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, list) or len(result) == 0 or not isinstance(result[0], list):
        raise ValueError(f"Unexpected HF feature-extraction batch response shape: {type(result)}")
    return result
