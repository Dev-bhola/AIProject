import os
import csv
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/golden-set")
@router.get("/golden-set/")
def get_golden_set():
    """Returns the golden set queries from data/golden_set.csv"""
    file_path = os.path.join("data", "golden_set.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Golden set data not found.")
        
    results = []
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    "sample_query": row.get("sample_query", ""),
                    "ground_truth_answer": row.get("ground_truth_answer", ""),
                    "source_document": row.get("source_document", ""),
                    "category": row.get("category", ""),
                    "page_reference": row.get("page_reference", "")
                })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read golden set: {e}")
