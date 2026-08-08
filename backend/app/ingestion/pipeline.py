import os
import json
import pickle
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rank_bm25 import BM25Okapi

from backend.app.ingestion.chunker import chunk_page
from backend.app.ingestion.embedder import embed_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_ingestion(parsed_dir: str):
    qdrant_url = os.environ.get("QDRANT_URL")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in environment variables")
        
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    collection_name = "legal_chunks"
    
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if not exists:
        logger.info(f"Creating Qdrant collection: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
    else:
        logger.info(f"Qdrant collection '{collection_name}' already exists.")

    all_chunks = []
    
    for filename in os.listdir(parsed_dir):
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(parsed_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
            
        doc_id = doc_data["doc_id"]
        source_file = doc_data["source_file"]
        doc_type = doc_data["doc_type"]
        
        for page in doc_data.get("pages", []):
            page_number = page["page_number"]
            text = page["text"]
            
            page_chunks = chunk_page(text, page_number, doc_id)
            
            for chunk in page_chunks:
                chunk["source_file"] = source_file
                chunk["doc_type"] = doc_type
                all_chunks.append(chunk)

    if not all_chunks:
        logger.warning("No chunks generated. Is the parsed directory empty?")
        return

    logger.info(f"Generated {len(all_chunks)} total chunks. Starting embedding...")
    
    chunk_texts = [c["text"] for c in all_chunks]
    embeddings = embed_batch(chunk_texts)
    
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
    
    tokenized_corpus = [text.lower().split(" ") for text in chunk_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    data_dir = os.path.join(os.path.dirname(parsed_dir))
    index_path = os.path.join(data_dir, "bm25_index.pkl")
    corpus_path = os.path.join(data_dir, "bm25_corpus.pkl")
    
    with open(index_path, 'wb') as f:
        pickle.dump(bm25, f)
        
    with open(corpus_path, 'wb') as f:
        pickle.dump(all_chunks, f)
        
    logger.info(f"BM25 index saved to {index_path} and {corpus_path}.")
    logger.info("Ingestion pipeline completed successfully!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join("backend", ".env"))
    
    parsed_directory = os.path.join("data", "parsed")
    if not os.path.exists(parsed_directory):
        logger.error(f"Directory not found: {parsed_directory}")
    else:
        run_ingestion(parsed_directory)
