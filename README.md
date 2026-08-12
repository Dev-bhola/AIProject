# US Tax & Legal Research Assistant

A **Retrieval-Augmented Generation (RAG)** system for US tax and legal research.
Ask a natural-language question and get a **grounded answer with exact
citations** — source document and page number — over a corpus of 40 legal
documents spanning federal acts, court judgments, policy overviews, and IRS
tax publications. Also generates evidence-linked summaries of individual
documents under a hard LLM rate-limit budget.

Built for traceability over raw scale: **every citation is independently
verified against its source chunk before being returned** — a claim the
model can't back up is dropped, not shown.

**🔗 Live demo:** [aiproject-fd2m.onrender.com](https://aiproject-fd2m.onrender.com)

> **Design write-up:** [APPROACH.md](APPROACH.md) — what was built and why.
> **Evaluation results:** [docs/evaluation-report.md](docs/evaluation-report.md) — methodology, numbers, and what didn't work.

---

## Highlights

- **Hybrid retrieval** — dense vector search (Qdrant) + BM25 keyword search,
  fused with Reciprocal Rank Fusion (`RRF_K=60`). 82.2% Top-5 retrieval
  accuracy on a 50-question golden set.
- **Grounded generation** — every answer's citations are resolved against the
  actual retrieved chunks before being returned; a citation that can't be
  verified is silently dropped rather than shown to the user. **100% citation
  grounding** across the full evaluation.
- **Constrained-budget summarization** — a Map → Consolidate → Reduce
  pipeline that plans its own token budget against Groq's free-tier
  6,000-tokens-per-minute limit before making a single API call, and samples
  representatively across a whole document rather than just its first pages.
- **Honest truncation reporting** — summaries expose *why* they're partial
  (`representative_sample`, `budget_limit`, `batch_failure`,
  `consolidation_limit`), not just a bare `truncated: true/false`.
- **Self-created Golden Set + evaluation harness** — 50 questions generated
  from real document pages, verified against source text, scored for
  retrieval accuracy, faithfulness, and refusal behavior on unanswerable
  questions.

## Architecture

```
PDF corpus (40 docs: acts / judgments / pov / tax_docs)
        │
        ▼
   Parser + Chunker            standardized JSON schema, page-indexed
        │
        ├──▶ Vector index (Qdrant, all-MiniLM-L6-v2)
        └──▶ Keyword index (BM25)
                     │
                     ▼
              Hybrid Search (RRF fusion)
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   Q&A (Groq LLM)          Summarization (Map→Consolidate→Reduce)
   + citation validator     + token-budget planner + evidence validation
        │                         │
        ▼                         ▼
   Answer + citations       Summary + truncation_reasons
```

Full component-by-component breakdown (exact fields, mechanism notes) in
[APPROACH.md](APPROACH.md).

---

## Tech stack

| Concern | Choice |
|---|---|
| PDF parsing | `pdfplumber` (recovers printed page numbers, skips TOC pages) |
| Chunking | Fixed-size (900 chars / 150 overlap) with section-title heuristic |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim), local via `fastembed` |
| Vector DB | Qdrant (cloud) |
| Keyword search | BM25 (`rank_bm25`) |
| Fusion | Reciprocal Rank Fusion, `k=60` |
| LLM (deployed) | Groq `llama-3.1-8b-instant` |
| LLM (local dev) | Ollama `llama3.1` (`ENVIRONMENT=local` in `.env`) |
| Backend | FastAPI |
| Frontend | React 19 + Vite + Tailwind CSS |
| Evaluation | Custom golden-set harness + LLM-judge faithfulness/grounding checks |

---

## Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend)
- A [Qdrant](https://qdrant.tech/) instance (cloud or self-hosted) — URL + API key
- A [Groq](https://console.groq.com/) API key (free tier)
- Optional, for local dev without spending Groq budget: [Ollama](https://ollama.com/)
  running locally with `llama3.1` pulled

---

## Setup

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

```
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
GROQ_API_KEY=your_groq_api_key
HF_API_KEY=your_huggingface_api_key   # required in production — used for query-time embedding
ENVIRONMENT=production   # or "local" to route generation and embedding through Ollama/fastembed instead of Groq/HF
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 2. Ingest the corpus

```bash
python -m backend.app.ingestion.parser      # PDFs in data/raw/ → data/parsed/*.json
python -m backend.app.ingestion.pipeline    # parsed JSON → Qdrant + BM25 index
```

This drops and rebuilds the Qdrant collection from scratch — re-run it after
adding or changing documents in `data/raw/`.

### 3. Run the backend

```bash
uvicorn backend.app.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

---

## API reference

All routes are mounted under `/api`.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/query` | Grounded Q&A. Body: `{"query": "..."}` |
| `GET` | `/api/summarize/{doc_id}` | Evidence-grounded document summary |
| `GET` | `/api/documents` | List all indexed documents (id, source file, category) |
| `GET` | `/api/documents/{doc_id}/pdf` | Serve the raw PDF for a document |
| `GET` | `/api/golden-set` | Serve the golden-set questions as JSON |

**Example:**

```bash
curl -X POST https://aiproject-fd2m.onrender.com/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the Additional Medicare Tax rate?"}'
```

Response:

```json
{
  "answer": "The Additional Medicare Tax rate is 0.9% [1].",
  "grounded": true,
  "citations": [{"marker": 1, "source_file": "...", "page": "9", "chunk_id": "..."}],
  "sources_used": ["vector", "keyword"]
}
```

---

## Evaluation

The system is evaluated against a self-created 50-question golden set
(`data/golden_set.csv`, ~11–12 per category, plus 5 deliberately unanswerable
questions), generated by sampling real pages from the corpus and having a
local LLM produce a grounded question/answer pair per page.

```bash
python -m backend.scripts.evaluate
```

| Metric | Result |
|---|---|
| Top-1 Retrieval Accuracy | 44.4% |
| Top-3 Retrieval Accuracy | 71.1% |
| Top-5 Retrieval Accuracy | 82.2% |
| Content Agreement (faithfulness) | 77.8% |
| Refusal Accuracy (unanswerable questions) | 100.0% |
| Citation Grounding | 100.0% |

Full methodology, per-category breakdown, and an honest account of two
retrieval changes that were tried and reverted after measurement: see
[docs/evaluation-report.md](docs/evaluation-report.md).

---

## Project structure

```
backend/
├── app/
│   ├── ingestion/       parser.py, chunker.py, pipeline.py
│   ├── retrieval/       search.py (hybrid search + RRF)
│   ├── generation/      qa.py, summarizer.py, citation_validator.py
│   ├── api/routes/      query.py, summarize.py, documents.py, golden_set.py
│   ├── core/            config.py
│   └── models/          schemas.py
└── scripts/             evaluate.py, generate_golden_set.py
data/
├── raw/{acts,judgments,pov,tax_docs}/   source PDFs
├── parsed/                               parsed JSON (one per doc)
├── golden_set.csv                        evaluation golden set
└── eval_results.json                     latest evaluation run output
frontend/
└── src/components/       QAView, SummaryView, DocumentsView, GoldenSetView
docs/
└── evaluation-report.md
APPROACH.md
```

---

## Notes & limitations

- **Retrieval Top-1 is the soft spot** (44.4%) in a corpus where several
  documents share dense, overlapping vocabulary (multiple IRS publications,
  multiple U.S. Reports opinions) — Top-5 (82.2%) shows the correct chunk is
  usually findable, just not always ranked first.
- **Groq's free-tier 6,000 TPM limit** is the binding constraint on
  summarization: large documents are summarized from a representative sample,
  not their full text, and this is reported honestly via `truncation_reasons`
  rather than hidden.
- **Graph RAG** (relationship mapping between documents) is explicitly
  optional in the assignment and was not implemented — deprioritized in favor
  of validating the core hybrid-search and citation-grounding pipeline first.
- **CORS is restricted to `CORS_ORIGINS`**, not a wildcard. The deployed
  frontend and backend are served from the same origin, so this doesn't
  affect the app itself — but if the API is ever called cross-origin from a
  different host (a separately-hosted frontend, a browser-based test
  script), that origin needs to be added to `CORS_ORIGINS` on the deployed
  service.

See [docs/evaluation-report.md](docs/evaluation-report.md) for the full
evaluation writeup and [APPROACH.md](APPROACH.md) for design rationale.
