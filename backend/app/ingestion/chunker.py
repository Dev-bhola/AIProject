import re

def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    separators = ["\n\n", "\n", ". ", " "]
    
    for sep in separators:
        if sep in text:
            splits = text.split(sep)
            chunks = []
            current_chunk = ""
            
            for split in splits:
                if current_chunk:
                    candidate = current_chunk + sep + split
                else:
                    candidate = split
                    
                if len(candidate) <= chunk_size:
                    current_chunk = candidate
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    if len(split) > chunk_size:
                        sub_chunks = _split_text(split, chunk_size, overlap)
                        if sub_chunks:
                            chunks.extend(sub_chunks[:-1])
                            current_chunk = sub_chunks[-1]
                        else:
                            current_chunk = split
                    else:
                        current_chunk = split
            
            if current_chunk:
                chunks.append(current_chunk)
                
            if all(len(c) <= chunk_size for c in chunks) or sep == " ":
                return _merge_with_overlap(chunks, chunk_size, overlap, sep)
                
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]

def _merge_with_overlap(splits: list[str], chunk_size: int, overlap: int, sep: str) -> list[str]:
    merged_chunks = []
    i = 0
    while i < len(splits):
        current_chunk = splits[i]
        
        j = i + 1
        while j < len(splits):
            candidate = current_chunk + sep + splits[j]
            if len(candidate) <= chunk_size:
                current_chunk = candidate
                j += 1
            else:
                break
                
        merged_chunks.append(current_chunk)
        
        if j < len(splits):
            overlap_length = 0
            overlap_components = []
            for k in range(j - 1, i - 1, -1):
                part = splits[k] + (sep if overlap_components else "")
                if overlap_length + len(part) <= overlap:
                    overlap_components.insert(0, part)
                    overlap_length += len(part)
                else:
                    break
            
            if not overlap_components:
                i = j
            else:
                next_start = splits[j]
                candidate_next = "".join(overlap_components) + next_start
                if len(candidate_next) <= chunk_size:
                    splits[j] = candidate_next
                    i = j
                else:
                    i = j
        else:
            i = j
            
    return merged_chunks

from backend.app.core.config import settings

def chunk_page(text: str, page_number: int, doc_id: str, last_section: str = "Unknown Section", chunk_size: int | None = None, overlap: int | None = None) -> tuple[list[dict], str]:
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    raw_chunks = _split_text(text, chunk_size, overlap)
    
    final_chunks = []
    current_section = last_section
    
    for index, chunk_text in enumerate(raw_chunks):
        if not chunk_text.strip():
            continue
            
        # Heuristic section detection
        lines = chunk_text.strip().split('\n')
        for line in lines[:3]: # check first few lines
            line = line.strip()
            # If line is short, all caps, or starts with Section/Chapter/Part
            if (len(line) < 100 and line.isupper() and len(line) > 3) or \
               line.upper().startswith(("SECTION ", "CHAPTER ", "PART ", "SUBTITLE ", "ARTICLE ")):
                current_section = line
                break
            
        final_chunks.append({
            "chunk_id": f"{doc_id}_p{page_number}_c{index}",
            "doc_id": doc_id,
            "page_number": page_number,
            "text": chunk_text.strip(),
            "chunk_index": index,
            "section_title": current_section
        })
        
    return final_chunks, current_section
