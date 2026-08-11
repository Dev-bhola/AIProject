from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str

class SummaryPoint(BaseModel):
    point: str
    source_file: str
    page_number: int

class SummaryCitation(BaseModel):
    source_file: str
    page_numbers: list[int]

class OverallSummary(BaseModel):
    text: str
    citations: list[SummaryCitation]

class SummaryResponse(BaseModel):
    doc_id: str
    summary_points: list[SummaryPoint]
    overall_summary: OverallSummary
    truncated: bool
    truncation_reasons: list[str] = []
