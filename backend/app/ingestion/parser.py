import os
import json
import logging
import pdfplumber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_pdf(file_path: str, doc_type: str, doc_id: str) -> dict:
    source_file = os.path.basename(file_path)
    document_data = {
        "doc_id": doc_id,
        "source_file": source_file,
        "doc_type": doc_type,
        "pages": []
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text or len(text.strip()) < 20:
                    logger.warning(f"Skipping page {page_number} in {source_file}: text is empty or too short.")
                    continue
                
                document_data["pages"].append({
                    "page_number": page_number,
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
    
    for folder_name, doc_type in type_mapping.items():
        folder_path = os.path.join(input_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
            
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(folder_path, filename)
                doc_id = os.path.splitext(filename)[0]
                
                parsed_data = parse_pdf(file_path, doc_type, doc_id)
                
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
