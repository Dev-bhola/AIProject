import os
import google.generativeai as genai

def _configure_genai():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)

def embed(text: str) -> list[float]:
    _configure_genai()
    result = genai.embed_content(
        model="models/gemini-embedding-2",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
        
    _configure_genai()
    
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        result = genai.embed_content(
            model="models/gemini-embedding-2",
            content=batch_texts,
            task_type="retrieval_document"
        )
        all_embeddings.extend(result['embedding'])
        
    return all_embeddings
