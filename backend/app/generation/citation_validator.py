import re

REFUSAL_TEXT = "I could not find the answer in the provided legal sources."

def extract_markers(answer_text: str) -> list[int]:
    """
    Extract citation markers from formats:
    [1]
    [1][2]
    [1, 2]
    [1,2,3]
    Return sorted unique ints.
    """
    markers = set()
    for group in re.findall(r"\[([\d,\s]+)\]", answer_text):
        for num in re.findall(r"\d+", group):
            markers.add(int(num))
    return sorted(list(markers))

def is_exact_refusal(answer_text: str) -> bool:
    """
    True only if answer exactly equals the refusal text after whitespace normalization.
    """
    return answer_text.strip() == REFUSAL_TEXT

def validate(answer_text: str, sources: list[dict]) -> dict:
    """
    sources are numbered source metadata dicts:
    [{"marker": 1, "chunk_id": "...", ...}, ...]
    """
    is_refusal = is_exact_refusal(answer_text)
    used_markers = extract_markers(answer_text)
    has_citation = len(used_markers) > 0
    
    valid_markers = {s["marker"] for s in sources}
    invalid_markers = [m for m in used_markers if m not in valid_markers]
    
    grounded = False
    problem = None
    
    if is_refusal:
        grounded = True
    elif not is_refusal and not has_citation:
        grounded = False
        problem = "You made factual claims without providing a citation, or you failed to use the exact refusal phrase."
    elif len(invalid_markers) > 0:
        grounded = False
        problem = f"You hallucinated these citation markers that do not exist in the source list: {invalid_markers}."
    else:
        # has citation, no invalid markers, not exact refusal
        grounded = True
        
    resolved_citations = [s for s in sources if s["marker"] in used_markers]
    
    return {
        "grounded": grounded,
        "is_refusal": is_refusal,
        "has_citation": has_citation,
        "used_markers": used_markers,
        "invalid_markers": invalid_markers,
        "resolved_citations": resolved_citations,
        "problem": problem
    }
