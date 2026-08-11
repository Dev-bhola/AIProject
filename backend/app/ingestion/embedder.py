# Load the model once globally so it doesn't reload on every call
# all-MiniLM-L6-v2 is fast, lightweight, and creates 384-dimensional embeddings
_model = None

from backend.app.core.config import settings

def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _model

def embed(text: str) -> list[float]:
    model = _get_model()
    # fastembed returns a generator of numpy arrays, we extract the first one
    result = list(model.embed(text))[0]
    return result.tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
        
    model = _get_model()
    
    # fastembed handles batching natively and optimally, so we can just pass the list
    # and convert the resulting generator of numpy arrays into a list of floats.
    results = model.embed(texts)
    
    all_embeddings = [res.tolist() for res in results]
            
    return all_embeddings
