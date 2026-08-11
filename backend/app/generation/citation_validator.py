import re

REFUSAL_MARKER = "could not find the answer in the provided legal sources"

def extract_markers(answer_text):
    """Return the sorted unique set of citation numbers used in the answer.
    Handles all the formats LLMs actually emit: [1], [1][2], and comma/space
    separated groups like [1, 5] or [1,5]."""
    markers = set()
    for group in re.findall(r"\[([\d,\s]+)\]", answer_text):
        for num in re.findall(r"\d+", group):
            markers.add(int(num))
    return sorted(markers)

def is_refusal(answer_text):
    return REFUSAL_MARKER in answer_text.lower()

def validate(answer_text, sources):
    """sources: list of dicts each with a 'marker' int (1-based) and metadata.
    Returns a dict describing whether the answer is properly grounded."""
    valid_markers = {s["marker"] for s in sources}
    used = extract_markers(answer_text)
    invalid = [m for m in used if m not in valid_markers]
    refusal = is_refusal(answer_text)
    has_citation = len(used) > 0

    # grounded when: no fabricated markers, AND (it cited something OR it
    # properly refused because the answer wasn't in the sources)
    grounded = (len(invalid) == 0) and (has_citation or refusal)

    resolved = [s for s in sources if s["marker"] in used]
    return {
        "grounded": grounded,
        "used_markers": used,
        "invalid_markers": invalid,
        "has_citation": has_citation,
        "is_refusal": refusal,
        "resolved_citations": resolved,
    }
