def deduplicate_sources(retrieved_chunks: list[dict]) -> list[str]:
    sources = []
    for chunk in retrieved_chunks:
        source_info = f"{chunk.get('source_file')} (Page {chunk.get('page_number')})"
        if source_info not in sources:
            sources.append(source_info)
    return sources
