import os
import requests
from groq import Groq
from backend.app.core.config import settings
from backend.app.retrieval.search import hybrid_search
from backend.app.generation.citation_validator import validate

def generate_answer(query: str, retrieved_chunks: list[dict]) -> dict:
    """
    Returns a dict with:
    {
        "answer": str,
        "grounded": bool,
        "citations": list[dict],
        "is_refusal": bool
    }
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    
    context_blocks = []
    sources = []
    
    # Cap sources to max 4 to respect Groq free tier 6000 TPM limit
    top_chunks = retrieved_chunks[:4]
    
    for i, chunk in enumerate(top_chunks):
        marker = i + 1
        source_file = chunk.get("source_file", "Unknown Source")
        page_num = chunk.get("page_number", "?")
        section = chunk.get("section_title", "Unknown Section")
        text = chunk.get("parent_section_text", chunk.get("text", "")) # Fallback to text if parent not yet available
        
        context_blocks.append(f"[{marker}] Document: {source_file} | Section: {section} | Page: {page_num}\n{text}")
        
        sources.append({
            "marker": marker,
            "source_file": source_file,
            "doc_id": chunk.get("doc_id", ""),
            "section": section,
            "page": str(page_num),
            "chunk_id": chunk.get("chunk_id", "")
        })
        
    context_string = "\n\n".join(context_blocks)
    
    prompt = f"""
You are an expert legal AI assistant. Your task is to answer the user's query based ONLY on the provided document excerpts. 

CITATION RULES:
1. Only cite a source using brackets like [1] or [2] where the number is the marker for the document that ACTUALLY supports the specific claim next to it.
2. If you are not confident a claim is supported by a specific source, DO NOT include that claim in your answer at all. Omit it silently.
3. Never write about your own citation-checking process, uncertainty, or reasoning in the answer. Do not write phrases like "this claim has a missing identifier," "I could not find," "specifically," or any parenthetical commentary about sources. The answer must read as a clean, direct response — as if written by a knowledgeable assistant, not as a debugging log.
4. If NONE of the provided sources support any part of an answer to the question, respond only with the exact refusal phrase, nothing else: 'I could not find the answer in the provided legal sources.'
5. Complete every sentence you start. Do not cut off mid-sentence.
6. CRITICAL: Do NOT use your own knowledge. Never guess or infer from general knowledge.

Context Documents:
{context_string}

User Query: {query}
"""

    try:
        if settings.ENVIRONMENT == "local":
            res = requests.post(
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "llama3.1",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=120
            )
            res.raise_for_status()
            answer = res.json()["message"]["content"]
        else:
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            answer = chat_completion.choices[0].message.content
        
        val_result = validate(answer, sources)
        
        # Self-correction loop
        if not val_result["grounded"] and not val_result["is_refusal"]:
            problem = val_result.get("problem", "You failed citation validation.")
            correction_prompt = f"""
Your previous answer was invalid because {problem}.
Rewrite the answer using only the provided numbered sources.
Every factual sentence must end with a valid citation (e.g. [1], [2]).
Only use markers that appear in the source list.
If the sources do not contain the answer, reply exactly:
"I could not find the answer in the provided legal sources."
"""
            if settings.ENVIRONMENT == "local":
                res2 = requests.post(
                    "http://127.0.0.1:11434/api/chat",
                    json={
                        "model": "llama3.1",
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": answer},
                            {"role": "user", "content": correction_prompt}
                        ],
                        "stream": False
                    },
                    timeout=120
                )
                res2.raise_for_status()
                answer = res2.json()["message"]["content"]
            else:
                chat_completion_2 = client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": answer},
                        {"role": "user", "content": correction_prompt}
                    ],
                    model="llama-3.1-8b-instant",
                )
                answer = chat_completion_2.choices[0].message.content
                
            val_result = validate(answer, sources)
            
        return {
            "answer": answer,
            "grounded": val_result["grounded"],
            "citations": val_result["resolved_citations"],
            "is_refusal": val_result["is_refusal"]
        }
    except Exception as e:
        print(f"Query generation failed: {e}")
        return {
            "answer": f"Query generation failed: {e}",
            "grounded": False,
            "citations": [],
            "is_refusal": False
        }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join("backend", ".env"))
    
    test_query = "What is the objective of Milestone 1?"
    
    print(f"Running End-to-End Pipeline for query: '{test_query}'...\n")
    
    print("1. Retrieving chunks...")
    chunks = hybrid_search(test_query, top_k=3).results
    
    if not chunks:
        print("No chunks found. Is Qdrant and the BM25 index populated?")
    else:
        print(f"Retrieved {len(chunks)} chunks. Generating answer...\n")
        result = generate_answer(test_query, [dict(c) for c in chunks])
        
        print("--- FINAL AI ANSWER ---")
        print(result["answer"])
        print("\n--- GROUNDING ---")
        print(f"Grounded: {result['grounded']}")
        print(f"Citations: {result['citations']}")
