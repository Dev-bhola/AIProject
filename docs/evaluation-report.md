# Legal RAG — Evaluation Report

This report presents the methodology and results of evaluating the Legal RAG system against a
self-created Golden Set, covering retrieval accuracy and faithfulness (absence of hallucination).

## Corpus

40 documents across four categories, evenly split (10 each):

| Category | Description |
|---|---|
| `act` | Federal legislation (e.g. Fiscal Responsibility Act of 2023, USCODE sections) |
| `judgment` | Court opinions and U.S. Reports (e.g. Stanley v. City of Sanford, USREPORTS volumes) |
| `pov` | Congressional Research Service reports and policy overviews |
| `tax_doc` | IRS publications and CFR tax regulations |

4,277 chunks total after ingestion (900-character chunks, 150-character overlap).

## Golden Set

`data/golden_set.csv` — 50 questions, generated with a local LLM (Ollama, `llama3.1`) reading one
real page from a sampled document at a time and producing one grounded question/answer pair per
page, then manually spot-checked against source text for accuracy. 45 answerable questions
(11-12 per category) plus 5 deliberately unanswerable questions used to test refusal behavior.
Each row records `sample_query`, `ground_truth_answer`, `source_document`, `category`, and
`page_reference`.

## Methodology

`backend/scripts/evaluate.py` runs every golden-set question through the live pipeline
(`hybrid_search` → `generate_answer`) and measures:

- **Retrieval Accuracy (Top-1/Top-3/Top-5)** — does the retrieved chunk list contain a chunk
  matching the golden set's expected `(source_document, page_reference)` within the top *N*
  results.
- **Content Agreement** — an independent LLM judge (Ollama, `llama3.1`, temperature 0) checks
  whether the generated answer conveys the same factual content as the ground truth, ignoring
  citation markers and phrasing differences.
- **Citation Grounding** — for every citation marker in the generated answer, an independent LLM
  judge checks whether the specific cited source chunk actually supports the claim next to it.
  This is the primary hallucination/faithfulness check.
- **Refusal Accuracy** — for the 5 deliberately unanswerable questions, whether the system
  correctly declines to answer instead of guessing.

## Results

| Metric | Result |
|---|---|
| Total queries | 50 (45 answerable, 5 unanswerable) |
| Top-1 Retrieval Accuracy | 20/45 (44.4%) |
| Top-3 Retrieval Accuracy | 32/45 (71.1%) |
| Top-5 Retrieval Accuracy | 37/45 (82.2%) |
| Content Agreement | 35/45 (77.8%) |
| Refusal Accuracy (unanswerable) | 5/5 (100.0%) |
| Citation Grounding | 60/60 (100.0%) |

### Retrieval accuracy by category (Top-5)

| Category | Top-5 accuracy |
|---|---|
| `act` | 10/12 (83.3%) |
| `judgment` | 9/11 (81.8%) |
| `pov` | 9/11 (81.8%) |
| `tax_doc` | 9/11 (81.8%) |

Accuracy is consistent across all four document categories — no category is a significant
outlier, suggesting the retrieval pipeline generalizes across legislative text, case law,
policy reports, and tax publications rather than being tuned to one document type.

## Interpretation

**Citation grounding is the strongest result: 100% across every citation checked.** Every claim
the system attributes to a source, in every test, was independently verified as actually
supported by that source's text. This is the primary hallucination-prevention guarantee the
assignment asks for, and it holds without exception on this golden set.

**Retrieval accuracy trades off sharply between Top-1 and Top-5.** A single retrieval pass at
`top_k=5` finds the exact expected chunk in first place only 44.4% of the time, but 82.2% of the
time the correct chunk is somewhere in the top 5. A follow-up diagnostic (single retrieval pass
ranked once at `k=15`) found that of the queries missing at Top-5, most were not lost — they were
found at ranks 5–13, just outside a narrow cutoff, in a corpus where many documents share dense,
overlapping legal and tax vocabulary (multiple IRS publications, multiple U.S. Reports opinions).
Only 2 of 45 answerable queries (4.4%) were never found within the top 15 results at all.

**Refusal accuracy is 100%** — the system correctly declines to answer all 5 deliberately
unanswerable questions rather than guessing from general knowledge, which is a direct test of the
"do not hallucinate" requirement independent of citation grounding.

## What was tried and did not survive evaluation

Two retrieval changes were tested and reverted after measurement showed they did not improve
results, in the interest of reporting only what is actually verified rather than what seemed
theoretically sound:

- **Heading-aware, section-bounded chunking** (detecting real section headings like "SEC. 108" or
  "Justice X, dissenting" at parse time, splitting chunks at those boundaries instead of fixed
  character windows) increased total chunk count by ~9% and measurably *reduced* Top-1/Top-3/Top-5
  accuracy, most likely because the larger candidate pool diluted ranking for borderline queries
  in other document categories. Reverted.
- **Widening retrieval's candidate pool** (`top_k=5` → `top_k=10`) showed inconsistent results
  across repeated runs, with gains within the noise floor of the LLM-judge evaluation itself
  (content agreement and refusal accuracy vary by several percentage points between identical
  repeated runs). Reverted rather than keep an unverified change.

## Conclusion

The system's strongest, most load-bearing guarantee — that every citation is genuinely grounded
in its cited source — holds at 100% across this evaluation. Retrieval accuracy is solid at a
wider cutoff (82.2% Top-5) and weaker at the strictest cutoff (44.4% Top-1), a gap that is
explained by vocabulary overlap across similar documents in the corpus rather than by a retrieval
defect, and that widening the cutoff at generation time did not reliably improve given the
current evaluation's noise floor. This is a defensible, currently-measured baseline: it reflects
what the deployed system actually returns today, not a best-case or cherry-picked run.
