import re

BOILERPLATE_PHRASES = [
    "remove before printing",
    "for your records",
    "do not print",
    "this page intentionally left blank",
    "table of contents",
    "page left blank",
    "ok to print",
    "fileid:",
    "userid:",
    "xsl/xml",
    "catalog number",
    "get forms and other information faster and easier",
]

def _is_toc_like_line(line: str, min_len: int = 20) -> bool:
    if len(line) < min_len:
        return False
    dot_count = line.count(".")
    alpha_count = sum(1 for c in line if c.isalpha())
    digit_count = sum(1 for c in line if c.isdigit())
    if "........" in line:
        return True
    return dot_count > 10 and (digit_count / max(alpha_count, 1)) > 0.15

def preprocess_chunks(doc_chunks: list) -> tuple[list, int, int]:
    cleaned_chunks = []
    chunks_removed = 0
    chars_removed = 0

    for chunk in doc_chunks:
        original_text = chunk.get("text", "")
        lines = original_text.split('\n')
        kept_lines = []
        for line in lines:
            lower_line = line.lower()
            if any(bp in lower_line for bp in BOILERPLATE_PHRASES):
                chars_removed += len(line) + 1
                continue
            if re.match(r'^\s*(page\s+)?\d+(\s+of\s+\d+)?\s*$', lower_line):
                chars_removed += len(line) + 1
                continue
            if _is_toc_like_line(line):
                chars_removed += len(line) + 1
                continue
            kept_lines.append(line)

        new_text = "\n".join(kept_lines).strip()
        original_stripped_len = len(original_text.strip())
        if not new_text:
            chunks_removed += 1
            chars_removed += len(original_text)
            continue

        boilerplate_ratio = 1.0 - (len(new_text) / original_stripped_len) if original_stripped_len else 0.0

        if len(new_text) < original_stripped_len:
            new_chunk = chunk.copy()
            new_chunk["text"] = new_text
            new_chunk["_boilerplate_ratio"] = boilerplate_ratio
            cleaned_chunks.append(new_chunk)
        else:
            cleaned_chunks.append(chunk)

    return cleaned_chunks, chunks_removed, chars_removed

def select_anchors_and_expand(doc_chunks: list, char_cap: int) -> tuple[list, bool]:
    total_chars = sum(len(c.get("text", "")) for c in doc_chunks)
    if total_chars <= char_cap:
        return doc_chunks, False
        
    HIGH_SIGNAL_WORDS = {"holding", "issue", "court", "rule", "tax", "threshold", "deduction", "credit", "rpc", "statute", "liability", "judgment"}
    
    chunk_scores = []
    for idx, chunk in enumerate(doc_chunks):
        text_lower = chunk.get("text", "").lower()
        score = sum(1 for word in HIGH_SIGNAL_WORDS if word in text_lower)
        boilerplate_ratio = chunk.get("_boilerplate_ratio", 0.0)
        if boilerplate_ratio > 0.5:
            score -= 10
        chunk_scores.append((idx, score))
        
    avg_chunk_len = total_chars / len(doc_chunks) if doc_chunks else 1
    target_chunks = max(1, int(char_cap / avg_chunk_len))
    
    anchor_indices = set()
    num_anchors = max(1, target_chunks // 2)
    if num_anchors > len(doc_chunks):
        num_anchors = len(doc_chunks)
        
    step = len(doc_chunks) / num_anchors
    for i in range(num_anchors):
        region_start = int(i * step)
        region_end = int((i + 1) * step) if i < num_anchors - 1 else len(doc_chunks)
        region_scores = chunk_scores[region_start:region_end]
        if region_scores:
            best_idx = max(region_scores, key=lambda x: x[1])[0]
            anchor_indices.add(best_idx)
            
    selected_indices = set()
    accumulated_chars = 0
    frontiers = {idx: [idx-1, idx+1] for idx in anchor_indices}
    
    for idx in list(anchor_indices):
        chunk_len = len(doc_chunks[idx].get("text", ""))
        if accumulated_chars + chunk_len > char_cap:
            anchor_indices.remove(idx)
            del frontiers[idx]
            continue
        selected_indices.add(idx)
        accumulated_chars += chunk_len
        
    active_anchors = list(anchor_indices)
    
    while active_anchors and accumulated_chars < char_cap:
        added_in_round = False
        for anchor in active_anchors:
            if accumulated_chars >= char_cap:
                break
                
            right_idx = frontiers[anchor][1]
            if right_idx < len(doc_chunks) and right_idx not in selected_indices:
                chunk_len = len(doc_chunks[right_idx].get("text", ""))
                if accumulated_chars + chunk_len <= char_cap:
                    selected_indices.add(right_idx)
                    accumulated_chars += chunk_len
                    frontiers[anchor][1] += 1
                    added_in_round = True
            elif right_idx < len(doc_chunks) and right_idx in selected_indices:
                frontiers[anchor][1] += 1
                
            left_idx = frontiers[anchor][0]
            if left_idx >= 0 and left_idx not in selected_indices:
                chunk_len = len(doc_chunks[left_idx].get("text", ""))
                if accumulated_chars + chunk_len <= char_cap:
                    selected_indices.add(left_idx)
                    accumulated_chars += chunk_len
                    frontiers[anchor][0] -= 1
                    added_in_round = True
            elif left_idx >= 0 and left_idx in selected_indices:
                frontiers[anchor][0] -= 1
                
        if not added_in_round:
            break
            
    if not selected_indices:
        selected_indices.add(0)
        
    final_chunks = [doc_chunks[idx] for idx in sorted(list(selected_indices))]
    return final_chunks, True

def partition_into_batches(chunks: list, char_cap: int) -> list[list]:
    batches = []
    current_batch = []
    current_len = 0
    
    for chunk in chunks:
        text_len = len(chunk.get("text", ""))
        if current_len + text_len > char_cap and current_batch:
            batches.append(current_batch)
            current_batch = [chunk]
            current_len = text_len
        else:
            current_batch.append(chunk)
            current_len += text_len
            
    if current_batch:
        batches.append(current_batch)
        
    return batches
