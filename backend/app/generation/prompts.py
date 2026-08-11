def get_map_prompt(context_string: str) -> str:
    return f"""
You are an expert legal AI assistant. Your job is to extract highly substantive, information-dense facts from this specific section of a document.

Rules:
1. Extract only self-contained, substantive facts. A fact must be understandable without relying on an unspecified preceding sentence. It is better to return fewer high-quality facts than several technically correct but meaningless fragments.
2. Context & Completeness: Include enough context to explain what the rule applies to and the actual requirement, threshold, exception, or consequence when that information is present in the provided text. Do not invent missing context.
3. Prioritize: Substantive legal/tax rules, eligibility requirements, thresholds, amounts, deadlines, exceptions, rights, obligations, and materially important definitions.
4. Deprioritize: Amendment-history statements such as "added by Pub. L...", section/revision metadata, editorial notes, administrative/formatting text, isolated cross-references, and facts that cannot be meaningfully understood from the available evidence.
5. Information Density: Preserve exact numbers, dates, percentages, statutes, names, and terminology when they are substantive.
6. Each fact MUST include exactly one citation to a provided source and page number.

Return a JSON object exactly matching this structure:
{{
  "facts": [
    {{
      "text": "description of the fact...",
      "citations": [
        {{ "source_file": "filename.pdf", "page_number": 1 }}
      ]
    }}
  ]
}}
No markdown fences, just valid JSON.

Document Section:
{context_string}
"""


def get_consolidate_prompt(facts_text: str) -> str:
    return f"""
You are an expert legal AI assistant. Your job is to consolidate and deduplicate the following intermediate facts while strictly preserving their Evidence IDs.

Rules:
1. Merge related or duplicate facts into single, coherent points.
2. Retain all highly substantive information (exact amounts, percentages, dates, rules, named entities).
3. Do NOT invent new facts.
4. For every merged or retained fact, provide a list of ALL corresponding Evidence IDs that support it. DO NOT invent page numbers. Only output Evidence IDs (e.g., "batch_0_fact_1").

Return a JSON object exactly matching this structure:
{{
  "facts": [
    {{
      "text": "description of the fact...",
      "evidence_ids": ["batch_0_fact_1", "batch_3_fact_2"]
    }}
  ]
}}
No markdown fences, just valid JSON.

Intermediate Facts:
{facts_text}
"""


def get_reduce_prompt(facts_text: str, truncation_context: str) -> str:
    return f"""
You are an expert legal AI assistant. Write an information-dense final summary based EXCLUSIVELY on the provided consolidated facts.

Rules for Key Points (summary_points):
1. Use ONLY the provided facts. Do not invent facts, speculate, or fill gaps in the sampled document.
2. Prioritize clarity and semantic completeness over the number of points. Merge related facts into a smaller number of coherent points. Prefer approximately 4-7 strong final points when the evidence supports that many.
3. Do not create a point merely because an extracted fact exists. If a fact cannot be expressed clearly and accurately using the supplied evidence, omit it.
4. Preserve exact dollar amounts, percentages, thresholds, dates, deadlines, and specific named entities. Do not use vague phrases such as "if certain subsections applied", "appeared to", "may relate to", or "the practical implications are likely...".
5. Only output Evidence IDs for your citations. DO NOT invent page numbers (e.g., do not write [Source: p17, Page 6]). Only output the Evidence IDs listed with the facts you use.

Rules for Overall Summary (overall_summary):
6. Write a dense overall summary paragraph (approx 2-4 sentences). Describe the actual substantive subject matter represented by the available evidence, not simply concatenate facts.
7. For a legal case, prefer: Case/context → legal issue → governing rule → holding → consequence. For tax/regulatory, prefer: Subject → major rules/changes → thresholds/deadlines → practical implication.
8. {truncation_context} Do not use the truncation limitation as filler throughout the summary, state it concisely if at all.

Return a JSON object exactly matching this structure:
{{
  "summary_points": [
    {{
      "point": "description of the point...",
      "evidence_ids": ["batch_0_fact_1"]
    }}
  ],
  "overall_summary": "overall summary paragraph..."
}}
No markdown fences, just valid JSON.

Consolidated Facts:
{facts_text}
"""


def get_regen_prompt(valid_points_text: str, truncation_context: str) -> str:
    return f"""Write an information-dense overall summary paragraph (approximately 2-4 sentences) based EXCLUSIVELY on the points provided below. Do not add outside knowledge.
Describe the actual substantive subject matter represented by the available evidence, not simply concatenate facts. Do not speculate or fill gaps in the sampled document. Do not use vague phrases like "appeared to" or "may relate to".
For a legal case, prefer: Case/context → legal issue → governing rule → holding → consequence. For tax/regulatory: Subject → major rules/changes → thresholds/deadlines → practical implication.
{truncation_context}

Points:
{valid_points_text}"""
