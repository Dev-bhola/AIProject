import os
import json
import csv
import re
import random
import urllib.request

OLLAMA_MODEL = "llama3.1"
PARSED_DIR = os.path.join("data", "parsed")
OUTPUT_PATH = os.path.join("data", "golden_set.csv")
TARGET_TOTAL = 50
UNANSWERABLE_COUNT = 5
MIN_PAGE_CHARS = 400


def call_ollama(prompt: str) -> str:
    data = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        result = json.loads(response.read().decode())
        return result.get("response", "")


def extract_json_array(text: str):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end <= start:
        raise ValueError("No JSON array found in model output")
    return json.loads(text[start:end].strip())


def load_documents():
    docs = []
    for filename in sorted(os.listdir(PARSED_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(PARSED_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pages = [p for p in data.get("pages", []) if len(p.get("text", "").strip()) >= MIN_PAGE_CHARS]
        if not pages:
            continue
        docs.append({
            "doc_id": data["doc_id"],
            "source_file": data["source_file"],
            "category": data.get("category", ""),
            "pages": pages,
        })
    return docs


def build_plan(docs, target_total, unanswerable_count):
    by_category = {}
    for d in docs:
        by_category.setdefault(d["category"], []).append(d)

    answerable_target = target_total - unanswerable_count
    categories = sorted(by_category.keys())
    per_category_base = answerable_target // len(categories)
    remainder = answerable_target - per_category_base * len(categories)

    plan = []
    for i, cat in enumerate(categories):
        cat_docs = by_category[cat]
        n_questions = per_category_base + (1 if i < remainder else 0)
        n_docs = len(cat_docs)
        base_per_doc = n_questions // n_docs
        extra = n_questions - base_per_doc * n_docs
        random.shuffle(cat_docs)
        for j, d in enumerate(cat_docs):
            count = base_per_doc + (1 if j < extra else 0)
            if count > 0:
                plan.append((d, count))
    return plan


def generate_for_document(doc, n_questions):
    pages = doc["pages"]
    chosen_pages = random.sample(pages, min(n_questions, len(pages)))
    results = []

    for page in chosen_pages:
        page_number = page["page_number"]
        text = page["text"][:3000]

        prompt = f"""Based ONLY on the following single page of a legal/tax document, generate exactly 1 factual question and answer pair.

Rules:
- The question must be specific and answerable using ONLY the text below.
- The answer must be concise (1-2 sentences) and directly supported by the text.
- Do not reference "the page" or "this document" in the question; ask a natural standalone question.
- Output ONLY a valid JSON array with exactly one object. No explanation, no markdown fencing.

Example format:
[{{"query": "What is X?", "ground_truth_answer": "X is defined as..."}}]

Page text:
{text}
"""
        try:
            raw = call_ollama(prompt)
            pairs = extract_json_array(raw)
            if not pairs:
                continue
            pair = pairs[0]
            results.append({
                "sample_query": pair["query"].strip(),
                "ground_truth_answer": pair["ground_truth_answer"].strip(),
                "source_document": doc["source_file"],
                "category": doc["category"],
                "page_reference": page_number,
            })
        except Exception as e:
            print(f"  Failed on {doc['source_file']} page {page_number}: {e}")

    return results


def build_unanswerable_rows(count):
    pool = [
        {"sample_query": "What did the Supreme Court decide in Roe v. Wade?", "ground_truth_answer": "Not answerable from provided documents"},
        {"sample_query": "What is the minimum wage under the Fair Labor Standards Act?", "ground_truth_answer": "Not answerable from provided documents"},
        {"sample_query": "What are the requirements for obtaining a patent in the United States?", "ground_truth_answer": "Not answerable from provided documents"},
        {"sample_query": "How many amendments are in the US Constitution?", "ground_truth_answer": "Not answerable from provided documents"},
        {"sample_query": "What is the current federal corporate tax rate for foreign banks operating in Germany?", "ground_truth_answer": "Not answerable from provided documents"},
        {"sample_query": "What penalties does the GDPR impose for data breaches?", "ground_truth_answer": "Not answerable from provided documents"},
    ]
    random.shuffle(pool)
    rows = []
    for item in pool[:count]:
        rows.append({
            "sample_query": item["sample_query"],
            "ground_truth_answer": item["ground_truth_answer"],
            "source_document": "",
            "category": "unanswerable",
            "page_reference": "",
        })
    return rows


def generate_golden_set():
    if not os.path.exists(PARSED_DIR):
        print("No parsed data found.")
        return

    docs = load_documents()
    if not docs:
        print("No usable documents found in parsed directory.")
        return

    plan = build_plan(docs, TARGET_TOTAL, UNANSWERABLE_COUNT)

    golden_set = []
    for doc, n_questions in plan:
        print(f"Generating {n_questions} question(s) for {doc['source_file']} ({doc['category']})...")
        rows = generate_for_document(doc, n_questions)
        print(f"  Got {len(rows)} pair(s)")
        golden_set.extend(rows)

    golden_set.extend(build_unanswerable_rows(UNANSWERABLE_COUNT))

    random.shuffle(golden_set)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sample_query", "ground_truth_answer", "source_document", "category", "page_reference"],
        )
        writer.writeheader()
        writer.writerows(golden_set)

    print(f"\nGolden set saved to {OUTPUT_PATH} with {len(golden_set)} total queries.")


if __name__ == "__main__":
    generate_golden_set()
