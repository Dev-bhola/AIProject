import os
import json
import csv
import urllib.request

def call_ollama(prompt: str) -> str:
    data = json.dumps({"model": "llama3.1", "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/generate", data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        result = json.loads(response.read().decode())
        return result.get("response", "")

def generate_golden_set():
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

        source_file = doc_data["source_file"]
        all_text = "\n".join([p.get("text", "") for p in doc_data.get("pages", [])])

        truncated_text = all_text[:6000]

        prompt = f"""Based on the following legal document, generate exactly 8 distinct Question and Answer pairs.

Rules:
- Questions should be specific and factual, covering different parts of the document.
- Answers must be concise (1-3 sentences) and directly supported by the text.
- Cover a variety of topics from the document: definitions, rights, procedures, names, dates, penalties, etc.
- Output ONLY a valid JSON array. No explanation, no markdown fencing.

Example format:
[{{"query": "What is X?", "ground_truth_answer": "X is defined as..."}}]

Document:
{truncated_text}
"""
        try:
            print(f"Generating QA pairs for {filename}...")
            text = call_ollama(prompt)

            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                text = text[start:end]

            qa_pairs = json.loads(text.strip())
            for pair in qa_pairs:
                golden_set.append({
                    "query": pair["query"],
                    "ground_truth_answer": pair["ground_truth_answer"],
                    "source_document": source_file,
                    "page_number": ""
                })

            print(f"  Generated {len(qa_pairs)} pairs for {filename}")
        except Exception as e:
            print(f"  Failed to generate for {filename}: {e}")

    unanswerable = [
        {"query": "What is the penalty for filing a 1099-MISC form late under the CARES act?", "ground_truth_answer": "Not answerable from provided documents", "source_document": "", "page_number": ""},
        {"query": "What did the Supreme Court decide in Roe v. Wade?", "ground_truth_answer": "Not answerable from provided documents", "source_document": "", "page_number": ""},
        {"query": "How many amendments are in the US Constitution?", "ground_truth_answer": "Not answerable from provided documents", "source_document": "", "page_number": ""},
        {"query": "What is the minimum wage under the Fair Labor Standards Act?",  "ground_truth_answer": "Not answerable from provided documents", "source_document": "", "page_number": ""},
        {"query": "What are the requirements for obtaining a patent in the United States?", "ground_truth_answer": "Not answerable from provided documents", "source_document": "", "page_number": ""},
    ]
    golden_set.extend(unanswerable)

    output_path = os.path.join("data", "golden_set.csv")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["query", "ground_truth_answer", "source_document", "page_number"])
        writer.writeheader()
        writer.writerows(golden_set)

    print(f"\nGolden set saved to {output_path} with {len(golden_set)} total queries.")

if __name__ == "__main__":
    generate_golden_set()
