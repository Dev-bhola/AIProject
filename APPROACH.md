# Approach

A RAG system for the US Tax & Legal domain: ingest a mixed corpus of acts, court judgments,
policy overviews, and tax documents; answer natural-language questions with cited sources; and
summarize individual documents, all under a hard 6,000-tokens-per-minute rate limit on the free
Groq tier used for generation.

## 1. Ingestion & knowledge standardization

Every source PDF is parsed once into a single, consistent JSON shape, regardless of which of the
four categories (`act`, `judgment`, `pov`, `tax_doc`) it belongs to:

```json
{
  "doc_id": "fiscal_responsibility_act_of_2023",
  "source_file": "fiscal_responsibility_act_of_2023.pdf",
  "category": "act",
  "pages": [
    { "page_number": 12, "text": "..." }
  ]
}
```

This is the standardized knowledge structure the pipeline is built on: every downstream
component — chunker, embedder, BM25 index, hybrid search, citation validator — consumes and
produces the same shape, so a court judgment and an IRS publication are handled identically once
parsed. Page numbers are recovered from the *printed* page number in the PDF text (not just the
physical PDF page index), so citations point to the page a human reader would actually cite.

Pages are then split into overlapping chunks (900 characters, 150-character overlap), each
carrying a single consistent schema:

```json
{
  "chunk_id": "fiscal_responsibility_act_of_2023_p12_c0",
  "doc_id": "...", "source_file": "...", "category": "...",
  "page_number": 12, "chunk_index": 0,
  "section_title": "SEC. 101. DISCRETIONARY SPENDING LIMITS.",
  "text": "...", "parent_section_text": "..."
}
```

`parent_section_text` is a small-to-big window: a wider block of surrounding same-section text
attached to every chunk, used only at answer-generation time to give the LLM more context than
the narrow retrieved chunk alone, without changing what gets embedded or indexed for search.

## 2. Hybrid search

Every chunk is indexed two ways:

- **Vector search** — embedded (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim) and stored in
  Qdrant.
- **Keyword search** — indexed with BM25 (`rank_bm25`), serving the same role as an ELK-style
  keyword index without the operational overhead of running Elasticsearch for a project this
  size.

Both retrievers run per query, and their ranked lists are combined with Reciprocal Rank Fusion
(`RRF_K=60`), so a chunk that ranks well on either exact keyword match or semantic similarity
surfaces near the top, rather than requiring both signals to agree.

Query-time embedding calls the Hugging Face Inference API in production (ingestion embeds
locally, one-time, via `fastembed`, using the same model). If that call fails for any reason, it
raises rather than silently returning a corrupted embedding — the retrieval layer catches that
failure and degrades to keyword-only search for that query, reporting it honestly via
`sources_used`, instead of letting a bad vector poison the ranked results without any visible
sign that something went wrong.

## 3. Q&A and summarization

**Q&A** (`/api/query`): hybrid search retrieves candidates, the top 4 are passed to Groq
(`llama-3.1-8b-instant`) with numbered source markers, and every citation the model outputs is
validated against the actual retrieved chunk before being returned — an answer is never allowed to
cite a source it wasn't given.

**Summarization** (`/api/summarize/{doc_id}`) is the part of the system most shaped by the token
budget constraint. A 122-page document cannot be sent to a model with a 6,000-TPM ceiling in one
pass, so the pipeline:

1. **Samples representatively** — instead of just taking the first N characters, the document is
   divided into positional regions and the highest-signal chunk from each region is selected
   (using domain keywords: tax, deduction, statute, holding, etc.), then expanded outward, so a
   small sample still draws from across the whole document rather than one section.
2. **Plans a token budget up front** — before any API call is made, the pipeline calculates how
   many MAP batches fit inside the remaining budget after reserving tokens for the final
   synthesis step, and caps itself to that number rather than guessing and retrying.
3. **Runs Map → Consolidate → Reduce** — each sampled batch is summarized into evidence-linked
   facts (MAP), facts are merged and deduplicated if they exceed the context budget
   (Consolidate), and a final synthesis pass produces the summary (Reduce).
4. **Grounds every fact to real evidence** — each extracted fact carries an internal evidence ID
   tied to the exact source chunk it came from. Before the final summary is returned, every
   citation in it is resolved back to that evidence store and checked against the chunks that
   were actually, successfully processed. Unverified or invented evidence IDs are silently
   dropped rather than surfaced to the user.
5. **Reports why, not just that, something was incomplete** — the response includes a
   `truncated` flag plus a `truncation_reasons` list (`representative_sample`, `budget_limit`,
   `batch_failure`, `consolidation_limit`) so a caller can tell "we sampled by design" apart from
   "a batch failed," instead of one ambiguous boolean.

Rate-limit handling is a small, hand-written bounded retry (parses Groq's own suggested wait time
from its 429 response) rather than a general-purpose retry library — a batch that would need to
wait too long fails fast and is marked, rather than blocking the whole request for tens of
seconds.

## 4. Evaluation

A 50-question golden set (`data/golden_set.csv`) was generated by sampling real pages from the
corpus and having a local LLM produce one grounded question/answer pair per page, spot-checked
against source text. `backend/scripts/evaluate.py` runs every question through the live pipeline
and measures retrieval accuracy (Top-1/3/5), content agreement against ground truth, citation
grounding (an independent LLM judge checks each citation actually supports its claim), and
refusal accuracy on deliberately unanswerable questions. Full results and interpretation are in
[docs/evaluation-report.md](docs/evaluation-report.md).

## 5. What was deliberately not built

**Graph RAG** (explicitly optional in the assignment) was scoped but not implemented — the
corpus's document-to-document relationships (a judgment citing a prior case, an act referencing
a U.S. Code section) are exactly the kind of structure a knowledge graph would help represent
correctly, but it was deprioritized in favor of validating the core hybrid-search and
citation-grounding pipeline first.

Two retrieval changes were tried and reverted after evaluation showed they did not hold up:
heading-aware section-bounded chunking (regressed retrieval accuracy by diluting ranking across
a larger candidate pool) and widening the retrieval candidate pool from top_k=5 to top_k=10
(results were within the evaluation's own run-to-run noise floor). Both are described, with the
measured numbers, in the evaluation report rather than silently discarded.
