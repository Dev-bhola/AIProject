import os
import json
import pickle
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rank_bm25 import BM25Okapi

from backend.app.ingestion.chunker import chunk_page
from backend.app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def attach_parent_windows(chunks: list[dict], max_chars: int = 1500) -> list[dict]:
    for i, chunk in enumerate(chunks):
        current_len = len(chunk["text"])
        window_texts = [chunk["text"]]
        
        left = i - 1
        right = i + 1
        
        while current_len < max_chars and (left >= 0 or right < len(chunks)):
            if right < len(chunks) and chunks[right]["section_title"] == chunk["section_title"]:
                text_to_add = chunks[right]["text"]
                if current_len + len(text_to_add) <= max_chars:
                    window_texts.append(text_to_add)
                    current_len += len(text_to_add)
                    right += 1
                else:
                    right = len(chunks)
            else:
                right = len(chunks)
                
            if left >= 0 and chunks[left]["section_title"] == chunk["section_title"]:
                text_to_add = chunks[left]["text"]
                if current_len + len(text_to_add) <= max_chars:
                    window_texts.insert(0, text_to_add)
                    current_len += len(text_to_add)
                    left -= 1
                else:
                    left = -1
            else:
                left = -1
                
        chunk["parent_section_text"] = f"Section: {chunk.get('section_title', 'Unknown')}\n\n" + "\n\n".join(window_texts)
        
    return chunks

def run_ingestion(parsed_dir: str):
    qdrant_url = os.environ.get("QDRANT_URL")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in environment variables")
        
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60)
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if exists:
        logger.info(f"Dropping existing Qdrant collection: {collection_name}")
        client.delete_collection(collection_name=collection_name)
        
    logger.info(f"Creating Qdrant collection: {collection_name} with size {settings.EMBEDDING_DIMENSION}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=settings.EMBEDDING_DIMENSION, distance=Distance.COSINE),
    )

    all_chunks = []
    
    for filename in os.listdir(parsed_dir):
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(parsed_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
            
        doc_id = doc_data["doc_id"]
        source_file = doc_data["source_file"]
        category = doc_data.get("category", "")
        
        last_section = "Unknown Section"
        doc_chunks = []
        for page in doc_data.get("pages", []):
            page_number = page["page_number"]
            text = page["text"]

            page_chunks, last_section = chunk_page(text, page_number, doc_id, last_section)
            
            for chunk in page_chunks:
                chunk["source_file"] = source_file
                chunk["category"] = doc_data.get("category", "")
                doc_chunks.append(chunk)
                
        doc_chunks = attach_parent_windows(doc_chunks, max_chars=1500)
        all_chunks.extend(doc_chunks)

    if not all_chunks:
        logger.warning("No chunks generated. Is the parsed directory empty?")
        return

    logger.info(f"Generated {len(all_chunks)} total chunks. Starting embedding...")
    
    chunk_texts = [c["text"] for c in all_chunks]
    
    # HARDCODED LOCAL EMBEDDING FOR FAST INGESTION (0 API CALLS)
    logger.info("Initializing fastembed locally for 384-dimensional vectors...")
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    embeddings = []
    # fastembed returns a generator of numpy arrays
    results = model.embed(chunk_texts)
    for res in results:
        embeddings.append(res.tolist())
    
    logger.info("Embedding complete. Upserting to Qdrant...")
    
    points = []
    for i, chunk in enumerate(all_chunks):
        points.append(
            PointStruct(
                id=i,
                vector=embeddings[i],
                payload=chunk
            )
        )
        
    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=collection_name,
            points=points[i:i + batch_size]
        )
        
    logger.info("Qdrant upsert complete. Building BM25 index...")
    
    import re
    tokenized_corpus = [re.findall(r'\w+', text.lower()) for text in chunk_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    data_dir = os.path.join(os.path.dirname(parsed_dir))
    index_path = os.path.join(data_dir, "bm25_index.pkl")
    corpus_path = os.path.join(data_dir, "bm25_corpus.pkl")
    
    with open(index_path, 'wb') as f:
        pickle.dump(bm25, f)
        
    with open(corpus_path, 'wb') as f:
        pickle.dump(all_chunks, f)
        
    logger.info(f"BM25 index saved to {index_path} and {corpus_path}.")
    
    import hashlib
    from datetime import datetime, timezone
    file_list = sorted([f for f in os.listdir(parsed_dir) if f.endswith(".json")])
    hash_obj = hashlib.sha256("".join(file_list).encode('utf-8'))
    timestamp = datetime.now(timezone.utc).isoformat()
    corpus_version = f"{hash_obj.hexdigest()[:8]}_{timestamp}"
    
    version_path = os.path.join(data_dir, "corpus_version.json")
    with open(version_path, 'w', encoding='utf-8') as f:
        json.dump({"corpus_version": corpus_version}, f)
    
    logger.info(f"Corpus version {corpus_version} saved to {version_path}")
    
    client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=999999999,
                vector=[0.0] * settings.EMBEDDING_DIMENSION,
                payload={"corpus_version": corpus_version}
            )
        ]
    )
    logger.info("Qdrant sentinel point upserted.")

    logger.info("Ingestion pipeline completed successfully!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join("backend", ".env"))
    
    parsed_directory = os.path.join("data", "parsed")
    if not os.path.exists(parsed_directory):
        logger.error(f"Directory not found: {parsed_directory}")
    else:
        run_ingestion(parsed_directory)
