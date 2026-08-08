import os
import google.generativeai as genai
from backend.app.retrieval.search import hybrid_search

def generate_answer(query: str, retrieved_chunks: list[dict]) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
        
    genai.configure(api_key=api_key)
    
    context_blocks = []
    for chunk in retrieved_chunks:
        source_file = chunk.get("source_file", "Unknown Source")
        page_num = chunk.get("page_number", "?")
        text = chunk.get("text", "")
        
        context_blocks.append(f"[Source: {source_file}, Page {page_num}]\n{text}")
        
    context_string = "\n\n".join(context_blocks)
    
    prompt = f"""
You are an expert legal AI assistant. Your task is to answer the user's query based ONLY on the provided document excerpts. 

Rules:
1. You must base your answer strictly on the provided context.
2. You must cite your sources inline using the exact format: [source_file, Page X].
3. Do not include any external knowledge.
4. If the provided documents do not contain the answer, you must reply exactly with: 'I cannot answer this based on the provided documents.'

Context Documents:
{context_string}

User Query: {query}
"""

    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    response = model.generate_content(prompt)
    
    return response.text

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join("backend", ".env"))
    
    test_query = "What is the objective of Milestone 1?"
    
    print(f"Running End-to-End Pipeline for query: '{test_query}'...\n")
    
    print("1. Retrieving chunks...")
    chunks = hybrid_search(test_query, top_k=3)
    
    if not chunks:
        print("No chunks found. Is Qdrant and the BM25 index populated?")
    else:
        print(f"Retrieved {len(chunks)} chunks. Generating answer...\n")
        answer = generate_answer(test_query, chunks)
        
        print("--- FINAL AI ANSWER ---")
        print(answer)
