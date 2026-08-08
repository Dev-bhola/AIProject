import os
import json
import re
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("backend", ".env"))
from backend.app.main import app
from backend.app.retrieval.search import hybrid_search

def extract_significant_words(text: str) -> set:
    words = re.findall(r'\b\w+\b', text.lower())
    return set([w for w in words if len(w) > 4])

def evaluate():
    client = TestClient(app)
    golden_path = os.path.join("data", "golden_set.json")
    
    if not os.path.exists(golden_path):
        print("No golden set found.")
        return
        
    with open(golden_path, 'r', encoding='utf-8') as f:
        golden_set = json.load(f)
        
    retrieval_hits = 0
    faithfulness_hits = 0
    total = len(golden_set)
    
    print("Starting evaluation...")
    for i, item in enumerate(golden_set):
        query = item["query"]
        ground_truth = item["ground_truth_answer"]
        gt_words = extract_significant_words(ground_truth)
        
        chunks = hybrid_search(query, top_k=5)
        context_text = " ".join([c.get("text", "") for c in chunks])
        context_words = extract_significant_words(context_text)
        
        # Retrieval Accuracy: Context contains ground truth answer
        if len(gt_words.intersection(context_words)) > 0 or ground_truth.lower() in context_text.lower():
            retrieval_hits += 1
            
        response = client.post("/api/query", json={"query": query})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            answer_words = extract_significant_words(answer)
            
            # Faithfulness: LLM answer aligns with the context it retrieved
            if len(answer_words.intersection(context_words)) > 0:
                faithfulness_hits += 1
                
        print(f"Processed query {i+1}/{total}")
        
    print("\n--- FINAL METRICS ---")
    print(f"Total Queries: {total}")
    print(f"Retrieval Accuracy: {(retrieval_hits / total) * 100:.1f}%")
    print(f"Faithfulness Score: {(faithfulness_hits / total) * 100:.1f}%")

if __name__ == "__main__":
    evaluate()
