import os
import logging
import asyncio
import time
from groq import AsyncGroq
import backend.app.retrieval.search as search_module
from backend.app.models.schemas import SummaryResponse, SummaryPoint, SummaryCitation, OverallSummary

from backend.app.generation.prompts import get_map_prompt, get_consolidate_prompt, get_reduce_prompt, get_regen_prompt
from backend.app.generation.llm_client import call_llm_with_retries, parse_llm_json
from backend.app.generation.document_utils import preprocess_chunks, select_anchors_and_expand, partition_into_batches

logger = logging.getLogger(__name__)

MAX_SUMMARY_BATCHES = int(os.environ.get("MAX_SUMMARY_BATCHES", 10)) # Absolute upper bound ceiling
MAX_REDUCTION_LEVELS = 3
BATCH_CHAR_CAP = int(os.environ.get("BATCH_CHAR_CAP", 3500))
FINAL_CONTEXT_BUDGET = 30000
CONCURRENCY_LIMIT = int(os.environ.get("CONCURRENCY_LIMIT", 1))

GROQ_TPM_LIMIT = 6000
EFFECTIVE_TPM_BUDGET = int(os.environ.get("EFFECTIVE_TPM_BUDGET", 4500))

# Token Budget Constants
MAP_MAX_OUTPUT = 300
REDUCE_MAX_OUTPUT = 750
PROMPT_OVERHEAD = 250


async def _extract_batch_async(batch, batch_idx, client, sem, call_counter, stats):
    async with sem:
        context_blocks = []
        for chunk in batch:
            sf = chunk.get("source_file", "Unknown")
            pn = chunk.get("page_number", "?")
            text = chunk.get("text", "")
            context_blocks.append(f"[Source: {sf}, Page {pn}]\n{text}")
            
        context_string = "\n\n".join(context_blocks)
        prompt = get_map_prompt(context_string)
        
        try:
            chat_completion = await call_llm_with_retries(client, prompt, "map", call_counter, stats, response_format={"type": "json_object"}, max_tokens=MAP_MAX_OUTPUT)
            if not chat_completion:
                raise ValueError("LLM returned no completion.")
            data = parse_llm_json(chat_completion.choices[0].message.content)
            raw_facts = data.get("facts", [])
            processed_facts = []
            for i, f in enumerate(raw_facts):
                if not f.get("text") or not f.get("citations"):
                    continue
                processed_facts.append({
                    "evidence_id": f"batch_{batch_idx}_fact_{i}",
                    "text": f["text"],
                    "citations": f["citations"]
                })
            return processed_facts
        except Exception as e:
            logger.error(f"Failed to parse/extract batch {batch_idx}: {e}")
            raise


async def _consolidate_group_async(group_facts, group_idx, client, sem, call_counter, stats):
    async with sem:
        facts_text = "\n\n".join([f"Evidence ID: {f.get('evidence_ids', f.get('evidence_id'))}\n{f['text']}" for f in group_facts])
        prompt = get_consolidate_prompt(facts_text)
        
        try:
            chat_completion = await call_llm_with_retries(client, prompt, "consolidate", call_counter, stats, response_format={"type": "json_object"}, max_tokens=800)
            if not chat_completion:
                raise ValueError("LLM returned no completion.")
            data = parse_llm_json(chat_completion.choices[0].message.content)
            return data.get("facts", [])
        except Exception as e:
            logger.error(f"Failed to parse/consolidate group {group_idx}: {e}")
            raise


async def _consolidate_facts_async(facts, client, sem, call_counter, stats, char_cap=BATCH_CHAR_CAP, level=1):
    total_chars = sum(len(f.get("text", "")) for f in facts)

    # If the facts already fit safely within the final synthesis context limit, skip consolidation.
    if total_chars <= FINAL_CONTEXT_BUDGET:
        return facts, False

    if level > MAX_REDUCTION_LEVELS:
        logger.warning(f"Max reduction levels reached ({MAX_REDUCTION_LEVELS}). Truncating intermediate facts.")
        truncated_facts = []
        cur_len = 0
        for f in facts:
            if cur_len + len(f.get("text", "")) > char_cap:
                break
            truncated_facts.append(f)
            cur_len += len(f.get("text", ""))
        return truncated_facts, True
        
    # Split facts into groups that fit char_cap
    groups = []
    current_group = []
    current_len = 0
    for f in facts:
        text_len = len(f.get("text", ""))
        if current_len + text_len > char_cap and current_group:
            groups.append(current_group)
            current_group = [f]
            current_len = text_len
        else:
            current_group.append(f)
            current_len += text_len
    if current_group:
        groups.append(current_group)
        
    logger.info(f"Consolidating level {level}: {len(groups)} groups")
    tasks = [_consolidate_group_async(g, i, client, sem, call_counter, stats) for i, g in enumerate(groups)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    next_facts = []
    group_failed = False

    for i, res in enumerate(results):
        if isinstance(res, BaseException):
            logger.error(f"Consolidation group {i} failed: {res}")
            group_failed = True
            continue
        next_facts.extend(res)

    deeper_facts, deeper_truncated = await _consolidate_facts_async(next_facts, client, sem, call_counter, stats, char_cap, level + 1)
    return deeper_facts, (group_failed or deeper_truncated)


async def _synthesize_final_summary_async(consolidated_facts, client, truncation_context, call_counter, stats):
    facts_text = "\n\n".join([f"Evidence IDs: {f.get('evidence_ids', f.get('evidence_id'))}\n{f['text']}" for f in consolidated_facts])
    prompt = get_reduce_prompt(facts_text, truncation_context)
    
    try:
        chat_completion = await call_llm_with_retries(client, prompt, "reduce", call_counter, stats, response_format={"type": "json_object"}, max_tokens=REDUCE_MAX_OUTPUT, max_retries=2)
        if not chat_completion:
            raise ValueError("LLM returned no completion.")
        data = parse_llm_json(chat_completion.choices[0].message.content)
        return data
    except Exception as e:
        logger.error(f"Failed to parse final synthesis: {e}")
        return {
            "summary_points": [],
            "overall_summary": "The document was processed, but the final synthesis failed due to API rate limits (Too Many Requests). Please try again in a few seconds."
        }


async def summarize_document(doc_id: str) -> SummaryResponse:
    start_time = time.time()
    call_counter = {"map": 0, "consolidate": 0, "reduce": 0}
    stats = {
        "429_errors": 0,
        "total_wait_time": 0.0,
        "map_durations": [],
        "consolidate_durations": [],
        "reduce_durations": []
    }
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
        
    search_module.load_bm25()
    corpus = search_module.BM25_CORPUS
    if corpus is None:
        raise ValueError("BM25 corpus failed to load.")
    
    doc_chunks = [c for c in corpus if c.get("doc_id") == doc_id]
    if not doc_chunks:
        raise ValueError(f"Document '{doc_id}' not found in index.")
        
    doc_chunks.sort(key=lambda x: (x.get("page_number", 0), x.get("chunk_index", 0)))
    
    preprocessed_chunks, chunks_rm, chars_rm = preprocess_chunks(doc_chunks)
    doc_load_time = time.time() - start_time
    
    # --- GLOBAL TOKEN BUDGET PLANNER ---
    reduce_fixed_cost = PROMPT_OVERHEAD + REDUCE_MAX_OUTPUT
    est_map_input = BATCH_CHAR_CAP / 4.0
    cost_per_map = est_map_input + PROMPT_OVERHEAD + MAP_MAX_OUTPUT
    
    budget_for_maps = EFFECTIVE_TPM_BUDGET - reduce_fixed_cost
    calculated_n = int(budget_for_maps // cost_per_map)
    max_allowed_map_calls = min(MAX_SUMMARY_BATCHES, max(1, calculated_n))
    
    total_allowed_chars = max_allowed_map_calls * BATCH_CHAR_CAP
    sampled_chunks, truncated_by_sampling = select_anchors_and_expand(preprocessed_chunks, total_allowed_chars)
    
    batches = partition_into_batches(sampled_chunks, BATCH_CHAR_CAP)
    total_batches = len(batches)
    
    truncation_reasons = []
    if truncated_by_sampling:
        truncation_reasons.append("representative_sample")
    if total_batches > max_allowed_map_calls:
        logger.warning(f"Document exceeds budget constraints ({total_batches} > {max_allowed_map_calls}). Truncating further.")
        batches = batches[:max_allowed_map_calls]
        total_batches = len(batches)
        truncation_reasons.append("budget_limit")
        
    client = AsyncGroq(api_key=api_key, max_retries=0)
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    total_doc_chars = sum(len(c.get('text', '')) for c in doc_chunks)
    sampled_chars = sum(len(c.get('text','')) for c in sampled_chunks)
    
    logger.info(f"=== Summarization Start (Global Token Budget Management) ===")
    logger.info(f"Document: {doc_chunks[0].get('source_file', doc_id)} | Total Chars: {total_doc_chars}")
    logger.info(f"Budget TPM Limit: {GROQ_TPM_LIMIT} | Effective Target: {EFFECTIVE_TPM_BUDGET}")
    logger.info(f"Reserved Reduce Budget: ~{reduce_fixed_cost} tokens")
    logger.info(f"Estimated Cost per MAP: ~{int(cost_per_map)} tokens")
    logger.info(f"Calculated Safe MAP capacity: {calculated_n} batches (Capped at {max_allowed_map_calls})")
    logger.info(f"Representative Sampling: Kept {sampled_chars} chars across {total_batches} batches")
    
    # MAP PHASE
    tasks = [_extract_batch_async(batch, i, client, sem, call_counter, stats) for i, batch in enumerate(batches)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_facts = []
    global_evidence_map = {}
    valid_sources = set()
    
    successful_batches = 0
    failed_batches = []
    
    for i, res in enumerate(results):
        if isinstance(res, BaseException):
            logger.error(f"Batch {i} failed permanently: {res}")
            failed_batches.append(i)
            if "batch_failure" not in truncation_reasons:
                truncation_reasons.append("batch_failure")
            continue

        successful_batches += 1
        for chunk in batches[i]:
            valid_sources.add((chunk.get("source_file"), chunk.get("page_number")))

        for fact in res:
            all_facts.append(fact)
            global_evidence_map[fact["evidence_id"]] = fact["citations"]

    if not all_facts:
        logger.warning("No facts extracted from any batch.")
        return SummaryResponse(
            doc_id=doc_id,
            summary_points=[],
            overall_summary=OverallSummary(text="No substantive information could be extracted from this document.", citations=[]),
            truncated=bool(truncation_reasons),
            truncation_reasons=truncation_reasons
        )

    # CONSOLIDATE PHASE
    consolidated_facts, consolidation_truncated = await _consolidate_facts_async(all_facts, client, sem, call_counter, stats, BATCH_CHAR_CAP, 1)
    if consolidation_truncated and "consolidation_limit" not in truncation_reasons:
        truncation_reasons.append("consolidation_limit")

    # REDUCE PHASE
    truncated = bool(truncation_reasons)
    truncation_context = ""
    if truncated:
        truncation_context = " Note: You are only summarizing a representative sample of this document, selected from across its length due to API/token constraints, not a truncated prefix. Phrase your overall summary to reflect this honestly."
        
    final_data = await _synthesize_final_summary_async(consolidated_facts, client, truncation_context, call_counter, stats)
    
    # RESOLVE EVIDENCE IDs & CITATION VALIDATION
    summary_points = []
    overall_citations_map = {}
    
    original_points = final_data.get("summary_points", [])
    if not isinstance(original_points, list):
        original_points = []

    for p in original_points:
        if not isinstance(p, dict):
            continue
        evidence_ids = p.get("evidence_ids", [])
        if isinstance(evidence_ids, str):
            evidence_ids = [evidence_ids]
            
        resolved_citations = set()
        for eid in evidence_ids:
            if eid in global_evidence_map:
                for cit in global_evidence_map[eid]:
                    resolved_citations.add((cit.get("source_file"), cit.get("page_number")))
            else:
                logger.warning(f"Final summary returned unknown evidence ID: {eid}")
                
        valid_resolved = []
        for sf, pn in resolved_citations:
            try:
                pn_int = int(pn)
                if (sf, pn_int) in valid_sources:
                    valid_resolved.append((sf, pn_int))
                    if sf not in overall_citations_map:
                        overall_citations_map[sf] = set()
                    overall_citations_map[sf].add(pn_int)
                else:
                    logger.warning(f"Discarding unverified resolved citation: {sf} Page {pn_int}")
            except (ValueError, TypeError):
                continue
                
        if valid_resolved:
            sf, pn = valid_resolved[0]
            summary_points.append(SummaryPoint(point=p.get("point", ""), source_file=sf, page_number=pn))
        else:
            logger.warning(f"Discarding point with no valid resolved citations: '{p.get('point')}'")
            
    overall_text = final_data.get("overall_summary", "")
    if isinstance(overall_text, dict):
        overall_text = str(overall_text.get("text", ""))
    else:
        overall_text = str(overall_text)
        
    if not summary_points and original_points:
        logger.info("All final points discarded due to citation failure. Regenerating...")
        overall_text = "The document was processed, but no claims could be securely verified against the source text."
    elif len(summary_points) < len(original_points):
        logger.info("Some final points were discarded. Regenerating overall summary based ONLY on validated points.")
        valid_points_text = "\n".join([f"- {sp.point}" for sp in summary_points])
        
        regen_prompt = get_regen_prompt(valid_points_text, truncation_context)
        
        try:
            regen_completion = await call_llm_with_retries(client, regen_prompt, "reduce", call_counter, stats, max_tokens=REDUCE_MAX_OUTPUT, max_retries=2)
            if not regen_completion:
                raise ValueError("LLM returned no completion.")
            overall_text = regen_completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed regen final synthesis: {e}")
            overall_text = "The document was processed, but the final overall summary failed due to API rate limits (Too Many Requests). Please try again in a few seconds."

    citations = []
    for sf, pages in overall_citations_map.items():
        citations.append(SummaryCitation(
            source_file=sf,
            page_numbers=sorted(list(pages))
        ))
        
    overall_summary = OverallSummary(
        text=overall_text,
        citations=citations
    )
    
    total_time = time.time() - start_time
    
    avg_map = sum(stats["map_durations"]) / len(stats["map_durations"]) if stats["map_durations"] else 0
    avg_cons = sum(stats["consolidate_durations"]) / len(stats["consolidate_durations"]) if stats["consolidate_durations"] else 0
    avg_red = sum(stats["reduce_durations"]) / len(stats["reduce_durations"]) if stats["reduce_durations"] else 0
    
    logger.info(f"=== Summarization Diagnostic (Completion) ===")
    logger.info(f"Total Document Characters: {total_doc_chars}")
    logger.info(f"Total Batches Processed: {total_batches} (Batch char limit: {BATCH_CHAR_CAP})")
    logger.info(f"Global Target Budget TPM: {EFFECTIVE_TPM_BUDGET}")
    logger.info(f"Reserved Reduce Budget: ~{reduce_fixed_cost} tokens")
    logger.info(f"Estimated MAP Budget Used: ~{int(total_batches * cost_per_map)} tokens")
    
    logger.info(f"Document Load/Chunk Time: {doc_load_time:.2f}s")
    logger.info(f"Successful Map Batches: {successful_batches}, Failed Map Batches: {len(failed_batches)}")
    logger.info(f"Map Calls: {call_counter['map']} (Avg execution: {avg_map:.2f}s)")
    logger.info(f"Consolidate Calls: {call_counter['consolidate']} (Avg execution: {avg_cons:.2f}s)")
    logger.info(f"Reduce Calls: {call_counter['reduce']} (Avg execution: {avg_red:.2f}s)")
    logger.info(f"429 Responses: {stats['429_errors']}")
    logger.info(f"Total Time Spent Waiting/Retrying: {stats['total_wait_time']:.2f}s")
    logger.info(f"Total Execution Time: {total_time:.2f}s")
    logger.info(f"Total intermediate facts produced: {len(all_facts)}")
    logger.info(f"Final points extracted: {len(summary_points)}")
    logger.info(f"Truncated: {truncated} (Reasons: {truncation_reasons})")
    logger.info(f"============================================")

    return SummaryResponse(
        doc_id=doc_id,
        summary_points=summary_points,
        overall_summary=overall_summary,
        truncated=truncated,
        truncation_reasons=truncation_reasons
    )
