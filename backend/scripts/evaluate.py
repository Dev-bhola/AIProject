import os
import csv
import re
import json
from typing import Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("backend", ".env"))
from backend.app.retrieval.search import hybrid_search
from backend.app.generation.qa import generate_answer

def content_agreement(generated_answer: str, ground_truth: str) -> bool | None:
    """Calls the LLM to verify if the generated answer conveys the same factual information as the ground truth."""
    import json
    import re
    import requests
    
    prompt = f"""
You are a lenient factual judge. Determine if the Generated Answer conveys the same core factual information as the Ground Truth.

Rules:
- IGNORE all citation brackets like [Source: file.pdf, Page X] in the generated answer — they are not part of the factual content.
- The ground truth may be a single word, short phrase, or sentence fragment. If the generated answer is a full sentence that CONTAINS or PARAPHRASES that ground truth fact, mark it as true.
- A verbose, well-formed answer that includes the ground truth fact is CORRECT, even if it adds more detail.
- A one-word or short-phrase ground truth matched by a longer descriptive sentence is CORRECT.
- Only mark false if the generated answer is factually WRONG, directly contradicts the ground truth, or is completely missing the key named fact entirely.
- "I cannot answer" responses count as false ONLY when the ground truth is a real answerable fact.

Respond ONLY with valid JSON: {{"agrees": true}} or {{"agrees": false}}. No other text.

Generated Answer: "{generated_answer}"
Ground Truth: "{ground_truth}"
"""
        
    try:
        from backend.app.core.config import settings
        if settings.ENVIRONMENT == "local":
            response = requests.post(
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "llama3.1",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.0}
                },
                timeout=120
            )
            response.raise_for_status()
            response_text = response.json()['message']['content'].strip()
        else:
            import os
            from groq import Groq
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0
            )
            response_text = chat_completion.choices[0].message.content.strip()
        
        match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        json_str = match.group(1) if match else response_text
        
        try:
            result = json.loads(json_str)
            if "agrees" not in result:
                print(f"Judge parsing error: missing 'agrees' field. Raw response: {response_text}")
                return None
            return bool(result["agrees"])
        except json.JSONDecodeError as e:
            print(f"Content agreement JSON parse failed: {e}. Raw response: {response_text}")
            return None
    except Exception as e:
        print(f"Content agreement check failed: {e}")
        return None

def citation_grounded(generated_answer: str, marker: int, cited_chunk_text: str) -> bool | None:
    """Calls the LLM to verify if the cited text genuinely supports the claim."""
    import json
    import re
    import requests
    
    prompt = f"""
Look at the Generated Answer below, which contains citation markers like [{marker}].
Does the Source Text genuinely and factually support the specific claims that the answer attributes to marker [{marker}]?

Guidance:
- Only return false if the Source Text actually contradicts the claim or completely fails to mention it. 
- If the Source Text provides partial support or says the same thing in different words, return true.

Respond ONLY with valid JSON matching this exact structure: {{"grounded": true}} or {{"grounded": false}}. No other text.

Generated Answer: "{generated_answer}"
Citation Marker to Check: "[{marker}]"
Source Text: "{cited_chunk_text}"
"""
        
    try:
        from backend.app.core.config import settings
        if settings.ENVIRONMENT == "local":
            response = requests.post(
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "llama3.1",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.0}
                },
                timeout=120
            )
            response.raise_for_status()
            response_text = response.json()['message']['content'].strip()
        else:
            import os
            from groq import Groq
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0
            )
            response_text = chat_completion.choices[0].message.content.strip()
        
        match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        json_str = match.group(1) if match else response_text
        
        try:
            result = json.loads(json_str)
            if "grounded" not in result:
                print(f"Judge parsing error: missing 'grounded' field. Raw response: {response_text}")
                return None
            return bool(result["grounded"])
        except json.JSONDecodeError as e:
            print(f"Grounding JSON parse failed: {e}. Raw response: {response_text}")
            return None
    except Exception as e:
        print(f"Grounding check failed: {e}")
        return None

def evaluate():
    golden_path = os.path.join("data", "golden_set.csv")
    results_path = os.path.join("data", "eval_results.json")
    
    if not os.path.exists(golden_path):
        print("No golden set CSV found.")
        return
        
    golden_set = []
    with open(golden_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            golden_set.append(row)
            
    # Load existing results if any to avoid re-running expensive LLM calls
    results_cache = {}
    if os.path.exists(results_path):
        try:
            with open(results_path, 'r', encoding='utf-8') as f:
                cached_list = json.load(f)
                for item in cached_list:
                    results_cache[item.get('sample_query', item.get('query', ''))] = item
        except:
            pass

    top1_hits = 0
    top3_hits = 0
    top5_hits = 0
    answerable_queries = 0
    
    content_agreement_hits = 0
    refusal_hits = 0
    unanswerable_queries = 0
    
    total_citations_checked = 0
    grounded_citations = 0
    
    total_queries = len(golden_set)
    all_results = []
    
    print("Starting rigorous evaluation...")
    for i, item in enumerate(golden_set):
        query = item.get("sample_query", item.get("query", ""))
        ground_truth = item["ground_truth_answer"]
        is_unanswerable = ground_truth.lower().startswith("not answerable")
        
        result_entry: dict[str, Any] = {
            "query": query,
            "ground_truth": ground_truth,
            "is_unanswerable": is_unanswerable,
            "retrieval_hit": False,
            "content_agreement": False,
            "grounding_failures": [],
            "generated_answer": "",
            "retrieved_chunks": []
        }

        
        # Check cache
        if query in results_cache and "generated_answer" in results_cache[query]:
            print(f"[{i+1}] Using cached result for query...")
            cached = results_cache[query]
            if not is_unanswerable:
                answerable_queries += 1
                hit_idx = cached.get("hit_index", -1)
                if hit_idx != -1:
                    if hit_idx < 1: top1_hits += 1
                    if hit_idx < 3: top3_hits += 1
                    if hit_idx < 5: top5_hits += 1
            else:
                unanswerable_queries += 1
                if cached.get("content_agreement"): refusal_hits += 1
                
            if cached.get("content_agreement") and not is_unanswerable: 
                content_agreement_hits += 1
            
            grounding_failures = cached.get("grounding_failures", [])
            for gf in grounding_failures:
                print(f"  [!] Failed Grounding: Marker [{gf['citation']}]")
            
            total_citations_checked += cached.get("total_citations_checked", 0)
            grounded_citations += cached.get("grounded_citations", 0)
            
            if not cached.get("content_agreement"):
                print(f"  [!] Failed Content Agreement: Answer does not match ground truth.")
                
            all_results.append(cached)
            continue
            
        print(f"[{i+1}] Querying hybrid search...")
        search_res = hybrid_search(query, top_k=5)
        chunks = search_res.results
        print(f"[{i+1}] Hybrid search completed. Retrieved {len(chunks)} chunks.")
        context_text = " ".join([c.get("text", "") for c in chunks])
        result_entry["retrieved_chunks"] = [{"source": c.get("source_file"), "page": c.get("page_number"), "text": c.get("text")} for c in chunks]
        
        # 1. Retrieval Accuracy
        result_entry["hit_index"] = -1
        if is_unanswerable:
            unanswerable_queries += 1
        else:
            answerable_queries += 1
            expected_source = item.get("source_document", "").strip()
            expected_page = item.get("page_reference", item.get("page_number", ""))

            hit_idx = -1
            for j, chunk in enumerate(chunks):
                chunk_source = chunk.get("source_file", "")
                chunk_page = str(chunk.get("page_number", ""))

                if expected_source and expected_source in chunk_source:
                    if not expected_page or str(expected_page).strip() == chunk_page:
                        hit_idx = j
                        break

            if hit_idx != -1:
                result_entry["hit_index"] = hit_idx
                if hit_idx < 1: top1_hits += 1
                if hit_idx < 3: top3_hits += 1
                if hit_idx < 5: top5_hits += 1
                result_entry["retrieval_hit"] = True
                
        try:
            print(f"[{i+1}] Generating answer...")
            if not chunks:
                answer = {"answer": "I cannot answer this based on the provided documents.", "grounded": True, "citations": []}
            else:
                answer = generate_answer(query, chunks)
            
            if isinstance(answer, dict):
                answer_text = str(answer.get("answer", ""))
                citations = answer.get("citations", [])
                if not isinstance(citations, list):
                    citations = []
            else:
                answer_text = str(answer)
                citations = []
                
            print(f"[{i+1}] Answer generated.")
            result_entry["generated_answer"] = answer_text
                
            # 2. Content Agreement (Overall Faithfulness)
            if is_unanswerable:
                EXPECTED_REFUSAL = "i could not find the answer"
                if EXPECTED_REFUSAL in answer_text.lower().strip() or "i cannot answer" in answer_text.lower().strip():
                    refusal_hits += 1
                    result_entry["content_agreement"] = True
                    result_entry["retrieval_hit"] = True
                else:
                    print(f"  [!] Failed Content Agreement: Should have refused to answer.")
            else:
                print(f"[{i+1}] Checking content agreement...")
                agrees = content_agreement(answer_text, ground_truth)
                if agrees is True:
                    content_agreement_hits += 1
                    result_entry["content_agreement"] = True
                elif agrees is False:
                    print(f"  [!] Failed Content Agreement: Answer does not match ground truth.")
                elif agrees is None:
                    print(f"  [!] Judge parsing error for content agreement.")
                print(f"[{i+1}] Content agreement check completed.")
            
            # 3. Citation Grounding Check
            print(f"[{i+1}] Checking citation grounding...")
            q_citations_checked = 0
            q_grounded = 0
            
            for cit in citations:
                marker = cit.get("marker")
                cit_chunk_id = cit.get("chunk_id")
                    
                matching_chunk_text = ""
                for c in chunks:
                    if c.get("chunk_id") == cit_chunk_id:
                        matching_chunk_text = c.get("text", "")
                        break
                        
                if matching_chunk_text:
                    q_citations_checked += 1
                    total_citations_checked += 1
                    grounding_res = citation_grounded(answer_text, marker, matching_chunk_text)
                    if grounding_res is True:
                        grounded_citations += 1
                        q_grounded += 1
                    elif grounding_res is False:
                        print(f"  [!] Failed Grounding: Marker [{marker}] does not support the claims in the answer.")
                        result_entry["grounding_failures"].append({
                            "citation": str(marker),
                            "source_text": matching_chunk_text
                        })
                    elif grounding_res is None:
                        print(f"  [!] Judge parsing error for grounding.")
            
            result_entry["total_citations_checked"] = q_citations_checked
            result_entry["grounded_citations"] = q_grounded
                                
        except Exception as e:
            print(f"Query generation failed: {e}")
                                
        print(f"Processed query {i+1}/{total_queries}")
        all_results.append(result_entry)
        
        # Save incrementally
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)
        
    print("\n--- FINAL METRICS ---")
    print(f"Total Queries: {total_queries} (Answerable: {answerable_queries}, Unanswerable: {unanswerable_queries})")
    
    if answerable_queries > 0:
        print(f"Top-1 Retrieval Accuracy: {top1_hits}/{answerable_queries} ({(top1_hits / answerable_queries) * 100:.1f}%)")
        print(f"Top-3 Retrieval Accuracy: {top3_hits}/{answerable_queries} ({(top3_hits / answerable_queries) * 100:.1f}%)")
        print(f"Top-5 Retrieval Accuracy: {top5_hits}/{answerable_queries} ({(top5_hits / answerable_queries) * 100:.1f}%)")
        print(f"Content Agreement (Answerable): {content_agreement_hits}/{answerable_queries} ({(content_agreement_hits / answerable_queries) * 100:.1f}%)")
        
    if unanswerable_queries > 0:
        print(f"Refusal Accuracy (Unanswerable): {refusal_hits}/{unanswerable_queries} ({(refusal_hits / unanswerable_queries) * 100:.1f}%)")
    
    if total_citations_checked > 0:
        print(f"Citation Grounding: {grounded_citations}/{total_citations_checked} ({(grounded_citations / total_citations_checked) * 100:.1f}%)")
    else:
        print("Citation Grounding: 0/0 (No citations generated/found)")

if __name__ == "__main__":
    evaluate()
