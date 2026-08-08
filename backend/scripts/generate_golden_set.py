import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("backend", ".env"))

def generate_golden_set():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    parsed_dir = os.path.join("data", "parsed")
    if not os.path.exists(parsed_dir):
        print("No parsed data found.")
        return
        
    golden_set = []
    
    for filename in os.listdir(parsed_dir):
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(parsed_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
            
        all_text = "\n".join([p.get("text", "") for p in doc_data.get("pages", [])])
        
        prompt = f"""
Based on the following document, generate exactly 5 distinct Question and Answer pairs.
Output the result strictly as a JSON array of objects.
Each object must have exactly two keys: "query" and "ground_truth_answer".
The answer should be concise and factually based on the text.

Document:
{all_text}
"""
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            qa_pairs = json.loads(text.strip())
            for pair in qa_pairs:
                pair["source_file"] = doc_data["source_file"]
                golden_set.append(pair)
                
            print(f"Generated {len(qa_pairs)} pairs for {filename}")
        except Exception as e:
            print(f"Failed to generate for {filename}: {e}")
            
    output_path = os.path.join("data", "golden_set.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(golden_set, f, indent=2)
    print(f"Golden set saved to {output_path} with {len(golden_set)} total pairs.")

if __name__ == "__main__":
    generate_golden_set()
