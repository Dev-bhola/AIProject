from backend.app.ingestion.pipeline import attach_parent_windows

def test_small_to_big():
    chunks = [
        {"text": "Chunk 1", "section_title": "Section A"},
        {"text": "Chunk 2", "section_title": "Section A"},
        {"text": "Chunk 3", "section_title": "Section A"},
        {"text": "Chunk 4", "section_title": "Section B"},
    ]
    
    # Very small limit so it only fits 2 chunks max (Chunk text is 7 chars. 2 chunks = 14 chars. Limit = 15)
    processed = attach_parent_windows(chunks, max_chars=15)
    
    for c in processed:
        assert c["text"] in c["parent_section_text"], f"Original text missing from parent: {c}"
        assert c["parent_section_text"].startswith(f"Section: {c['section_title']}"), f"Wrong section header: {c}"
        
    print("Chunk 1 parent:", processed[0]["parent_section_text"])
    print("Chunk 4 parent:", processed[3]["parent_section_text"])
    print("All small-to-big tests passed!")

if __name__ == "__main__":
    test_small_to_big()
