import os
import json
import google.generativeai as genai

def summarize_document(doc_id: str, parsed_dir: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
        
    genai.configure(api_key=api_key)
    
    file_path = os.path.join(parsed_dir, f"{doc_id}.json")
    if not os.path.exists(file_path):
        return f"Document '{doc_id}' not found."
        
    with open(file_path, 'r', encoding='utf-8') as f:
        doc_data = json.load(f)
        
    all_text = []
    for page in doc_data.get("pages", []):
        all_text.append(page.get("text", ""))
        
    full_document_text = "\n\n".join(all_text)
    
    prompt = f"""
You are an expert legal AI assistant. Your task is to provide a concise, high-level summary of the following legal document.
Focus on the main objectives, key requirements, and overarching themes. Do not get bogged down in minute details.

Document Text:
{full_document_text}

Summary:
"""

    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    response = model.generate_content(prompt)
    
    return response.text
