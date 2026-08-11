import json
import logging
import re
import asyncio
import time

logger = logging.getLogger(__name__)

def parse_llm_json(response_text: str):
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return json.loads(response_text)

async def call_llm_with_retries(client, prompt, call_type, call_counter, stats, response_format=None, max_tokens=None, max_retries=1):
    base_wait = 2
    call_counter[call_type] += 1
    
    start_time = time.time()
    for attempt in range(max_retries + 1):
        try:
            kwargs = {
                "messages": [{"role": "user", "content": prompt}],
                "model": "llama-3.1-8b-instant",
            }
            if response_format:
                kwargs["response_format"] = response_format
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
                
            completion = await client.chat.completions.create(**kwargs)
            duration = time.time() - start_time
            stats[f"{call_type}_durations"].append(duration)
            return completion
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Too Many Requests" in err_str:
                stats["429_errors"] += 1
                
            if attempt == max_retries:
                raise
                
            match = re.search(r"try again in ([\d\.]+)s", err_str)
            if match:
                wait_time = float(match.group(1)) + 0.5
            else:
                wait_time = min(base_wait * (2 ** attempt), 5) # max 5s backoff
                
            if wait_time > 5.0 and call_type == "map":
                logger.warning(f"[{call_type}] 429 Retry-after is too long ({wait_time}s). Failing fast to prevent blocking.")
                raise
                
            logger.warning(f"[{call_type}] API error (attempt {attempt+1}): {e}. Retrying in {wait_time:.2f}s...")
            
            stats["total_wait_time"] += wait_time
            await asyncio.sleep(wait_time)
            call_counter[call_type] += 1 # A retry implies another API call is made
