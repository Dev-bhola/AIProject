from sentence_transformers import SentenceTransformer

# Load the model once globally so it doesn't reload on every call
# all-MiniLM-L6-v2 is fast, lightweight, and creates 384-dimensional embeddings
_model = None

from backend.app.core.config import settings

def _get_model():
    global _model
    if _model is None:
        # We can suppress the huggingface symlink warning if it happens, 
        # but it's just a warning.
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def embed(text: str) -> list[float]:
    model = _get_model()
    # encode() returns a numpy array, we convert to list of floats
    result = model.encode(text)
    return result.tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
        
    model = _get_model()
    
    # SentenceTransformer handles batching internally, but we can just pass the whole list
    # or pass it in chunks to avoid memory spikes if the list is huge.
    # 3000 chunks is very small for local models, we can pass it directly or in batches of 256.
    
    batch_size = 256
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        print(f"Embedding batch {i//batch_size + 1} / {(len(texts) + batch_size - 1)//batch_size} (size: {len(batch_texts)})")
        
        # encode returns a numpy array of shape (batch_size, 384)
        results = model.encode(batch_texts)
        
        for res in results:
            all_embeddings.append(res.tolist())
            
    return all_embeddings
