import os
import json
import logging
import pdfplumber
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _is_toc_page(text: str) -> bool:
    if '........' in text:
        return True
    alpha_count = sum(1 for c in text if c.isalpha())
    digit_count = sum(1 for c in text if c.isdigit())
    if alpha_count > 0 and digit_count / alpha_count > 0.25:
        return True
    return False

def extract_printed_page(text: str) -> int | None:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return None
        
    candidates = lines[:4] + lines[-4:]
    for line in candidates:
        line_clean = line.strip().lower()
        match = re.match(r'^\s*(?:page\s*)?(?:-?\s*)?(\d+)(?:\s*-)?(?:\s*of\s*\d+)?\s*$', line_clean)
        if match:
            return int(match.group(1))
    return None

def parse_pdf(file_path: str, category: str, doc_id: str) -> dict:
    source_file = os.path.basename(file_path)
    document_data = {
        "doc_id": doc_id,
        "source_file": source_file,
        "category": category,
        "pages": []
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            last_confirmed = 0
            offset = 0
            
            for physical_idx, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text or len(text.strip()) < 20:
                    logger.warning(f"Skipping page {physical_idx} in {source_file}: text is empty or too short.")
                    continue
                    
                if _is_toc_page(text):
                    logger.info(f"Skipping page {physical_idx} in {source_file}: detected as TOC/index page.")
                    continue
                
                detected = extract_printed_page(text)
                final_page = physical_idx
                
                if detected is not None:
                    if last_confirmed and detected <= last_confirmed:
                        logger.warning(f"[{source_file}] Detected page {detected} goes backward from {last_confirmed}. Using offset {offset}")
                        final_page = physical_idx + offset
                    elif last_confirmed and detected > last_confirmed + 5: 
                        logger.warning(f"[{source_file}] Detected page {detected} jumps too far from {last_confirmed}. Using offset {offset}")
                        final_page = physical_idx + offset
                    else:
                        offset = detected - physical_idx
                        final_page = detected
                        last_confirmed = detected
                else:
                    final_page = physical_idx + offset
                    logger.debug(f"[{source_file}] No printed page found on physical {physical_idx}. Using offset {offset}")
                
                document_data["pages"].append({
                    "page_number": final_page,
                    "text": text.strip()
                })
    except Exception as e:
        logger.error(f"Failed to parse {source_file}: {e}")
        
    return document_data

def parse_directory(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    type_mapping = {
        "acts": "act",
        "judgments": "judgment",
        "pov": "pov",
        "tax_docs": "tax_doc"
    }
    
    for folder_name, category in type_mapping.items():
        folder_path = os.path.join(input_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
            
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(folder_path, filename)
                doc_id = os.path.splitext(filename)[0]
                
                parsed_data = parse_pdf(file_path, category, doc_id)
                
                if parsed_data["pages"]:
                    output_file = os.path.join(output_dir, f"{doc_id}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Successfully parsed and saved {filename} to {output_file}")
                else:
                    logger.warning(f"No pages parsed for {filename}, skipping JSON generation.")

if __name__ == "__main__":
    raw_dir = os.path.join("data", "raw")
    parsed_dir = os.path.join("data", "parsed")
    parse_directory(raw_dir, parsed_dir)
