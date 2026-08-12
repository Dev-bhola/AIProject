# Architecture Diagram

PDF → Parsing → Hybrid Search → LLM, showing the actual data shapes and decision points at each
stage. Rendered with Mermaid (renders natively on GitHub; also plain text, so it's directly
readable by tooling or another model without an image).

## Ingestion pipeline

```mermaid
flowchart TD
    A["PDF files\ndata/raw/{acts,judgments,pov,tax_docs}/"] -->|"pdfplumber.extract_text()"| B["Parser\nparser.py"]
    B -->|"recovers printed page number\nskips TOC/index pages"| C["Parsed JSON\n{doc_id, source_file, category,\npages: [{page_number, text}]}"]
    C -->|"900 char / 150 overlap"| D["Chunker\nchunker.py"]
    D -->|"heuristic section labeling"| E["Chunk records\n{chunk_id, page_number, section_title,\ntext, parent_section_text}"]
    E -->|"embed each chunk"| F["fastembed\nall-MiniLM-L6-v2, 384-dim"]
    E -->|"tokenize each chunk"| G["BM25Okapi index\nrank_bm25"]
    F -->|"upsert vectors + payload"| H[("Qdrant\nvector store")]
    G -->|"pickle"| I[("bm25_index.pkl\nbm25_corpus.pkl")]
```

## Query-time flow (Q&A)

```mermaid
flowchart LR
    Q["User query"] --> R["hybrid_search()\nsearch.py"]
    R -->|"top_k*4 candidates"| V["Vector search\nQdrant cosine similarity"]
    R -->|"top_k*4 candidates"| K["Keyword search\nBM25 score"]
    V --> F["Reciprocal Rank Fusion\nRRF_K=60"]
    K --> F
    F -->|"page-diversity cap:\nmax 2 chunks per page"| C["Top-5 ranked chunks"]
    C -->|"top 4 chunks, numbered [1]-[4]"| G["generate_answer()\nqa.py"]
    G -->|"prompt + context"| L["Groq\nllama-3.1-8b-instant"]
    L -->|"answer with [n] citations"| V2["citation_validator.validate()"]
    V2 -->|"unresolvable citation? not grounded"| RC{"grounded?"}
    RC -->|"no"| SC["self-correction retry\n(1 extra Groq call)"]
    RC -->|"yes"| OUT["Response:\nanswer + citations\n(source_file, page_number)"]
    SC --> OUT
```

## Summarization flow (Map → Consolidate → Reduce)

```mermaid
flowchart TD
    DOC["doc_id"] --> LOAD["Load all chunks for document\nfrom BM25 corpus"]
    LOAD --> BUDGET["Token budget planner\nEFFECTIVE_TPM_BUDGET=4500\nreserve tokens for REDUCE"]
    BUDGET -->|"max_allowed_map_calls"| SAMPLE["Representative sampler\nselect_anchors_and_expand()\nregion-based anchor + expand"]
    SAMPLE -->|"sampled chunks, N batches"| MAP["MAP phase\nN parallel Groq calls\n(concurrency limit = 1)"]
    MAP -->|"facts + evidence_id per fact"| EV[("Evidence map\n{evidence_id: citations}")]
    MAP --> CONS{"total facts\n> FINAL_CONTEXT_BUDGET?"}
    CONS -->|"yes"| CONSOLIDATE["Consolidate phase\nmerge/dedupe facts\n(recursive, capped depth)"]
    CONS -->|"no"| REDUCE
    CONSOLIDATE --> REDUCE["REDUCE phase\n1 Groq call\nfinal summary_points + overall_summary"]
    REDUCE -->|"evidence_ids per point"| VALIDATE["Resolve evidence_ids against\nEV + valid_sources set"]
    VALIDATE -->|"invalid/unresolved? drop the point"| RESULT["Response:\nsummary_points + overall_summary\ntruncated + truncation_reasons"]
```

## Notes on what the arrows mean

- **Parsing → Chunking**: the parser's output is the standardized knowledge structure — every
  category (act/judgment/pov/tax_doc) produces the exact same JSON shape, so nothing downstream
  needs to special-case document type.
- **RRF fusion**: neither the vector nor keyword ranker "wins" — a chunk ranking well on *either*
  signal surfaces near the top of the fused list, which is why the diagram shows both retrievers
  feeding one fusion step rather than an if/else choice between them.
- **Citation validation is a hard gate, not a suggestion**: in both the Q&A and summarization
  flows, a citation that cannot be resolved back to a real, retrieved chunk is removed from the
  output rather than trusted — this is what makes "every response includes accurate legal
  citations" an enforced property instead of a hope.
- **The token budget planner runs before any Groq call is made** in the summarization flow — the
  number of MAP batches is a calculated ceiling based on the 6,000 TPM limit, not a number chosen
  by trial and error.
