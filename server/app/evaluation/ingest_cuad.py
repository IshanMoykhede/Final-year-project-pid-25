import os
import tempfile
import asyncio
import logging
from uuid import uuid4

# Setup standard logging for the script
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from app.core.supabase import connectSupa
from app.services.chunking_service import chunk_document
from app.services.classification_service import process_document_classification
from app.services.embedding_service import generate_embeddings

# We will try to import datasets, if it's not installed, we'll guide the user.
try:
    from datasets import load_dataset
except ImportError:
    logger.error("The 'datasets' library is required to download CUAD.")
    logger.error("Please run: pip install datasets")
    exit(1)

async def run_pipeline(file_id: str):
    logger.info(f"Step 1/3: Chunking document {file_id}...")
    chunk_res = chunk_document(file_id)
    chunks_count = len(chunk_res) if isinstance(chunk_res, list) else getattr(chunk_res, 'chunks', 0)
    logger.info(f"Created {chunks_count} chunks.")

    logger.info(f"Step 2/3: Classifying chunks and detecting cross-references...")
    class_res = process_document_classification(file_id)
    processed_count = class_res.get("total_chunks_processed", 0) if isinstance(class_res, dict) else 0
    logger.info(f"Classification completed for {processed_count} chunks.")

    logger.info(f"Step 3/3: Generating embeddings...")
    embed_res = generate_embeddings(file_id)
    logger.info(f"Embeddings generation finished: {embed_res}")


async def main():
    supabase = connectSupa()

    # Get existing user_id
    user_res = supabase.table("files").select("user_id").limit(1).execute()
    if not user_res.data:
        logger.error("No existing files found in database to extract user_id from. Please create a user or upload at least one file first.")
        return
    user_id = user_res.data[0]["user_id"]
    logger.info(f"Using User ID: {user_id}")

    logger.info("Downloading CUAD dataset from HuggingFace (theatticusproject/cuad)...")
    # In datasets, theatticusproject/cuad returns rows with a 'pdf' feature containing a pdfplumber.PDF object!
    dataset = load_dataset(
        "theatticusproject/cuad", 
        split="train", 
        verification_mode="no_checks"
    )
    
    unique_contexts = []
    titles = []
    
    logger.info("Extracting contract text from CUAD PDF objects...")
    for idx, item in enumerate(dataset):
        pdf_obj = item.get("pdf")
        if not pdf_obj:
            continue
            
        # Extract text from all pages in this contract
        text_parts = []
        for page in pdf_obj.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        
        full_text = "\n\n".join(text_parts).strip()
        
        if len(full_text) > 1000:
            title = f"Contract_{idx+1}"
            unique_contexts.append(full_text)
            titles.append(title)
            logger.info(f"Loaded {title} ({len(full_text)} characters, {len(pdf_obj.pages)} pages)")
            
        if len(unique_contexts) >= 3:
            break

    logger.info(f"Found {len(unique_contexts)} contracts to ingest: {titles}")

    for idx, (title, context) in enumerate(zip(titles, unique_contexts), 1):
        file_id = str(uuid4())
        filename = f"CUAD_{title[:30]}_{idx}.txt"
        storage_path = f"{user_id}/{file_id}.txt"
        
        logger.info(f"[{idx}/3] Uploading {filename} to Supabase Storage...")
        
        # Save locally to a temp file and upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(context)
            tmp_path = tmp.name
            
        try:
            with open(tmp_path, "rb") as f:
                supabase.storage.from_("Files").upload(storage_path, f)
                
            # Prepare raw_items structure that chunking_service expects from OCR
            # Prepare raw_items structure that chunking_service expects
            import re
            paragraphs = [p.strip() for p in context.split("\n\n") if p.strip()]
            items = []
            for p in paragraphs:
                lines = [l.strip() for l in p.split("\n") if l.strip()]
                if lines and len(lines[0]) < 120 and re.match(r'^(ARTICLE|SECTION|CLAUSE|\d+(\.\d+)*)\b', lines[0], re.I):
                    items.append({"type": "heading", "md": lines[0], "text": lines[0], "bbox": None})
                    body = "\n".join(lines[1:])
                    if body:
                        items.append({"type": "paragraph", "md": body, "text": body, "bbox": None})
                else:
                    items.append({"type": "paragraph", "md": p, "text": p, "bbox": None})

            raw_items = {
                "pages": [
                    {
                        "page_number": 1,
                        "items": items
                    }
                ]
            }

            # Insert into files table to match your exact schema diagram
            supabase.table("files").insert({
                "id": file_id,
                "user_id": user_id,
                "file_name": filename,
                "storage_path": storage_path,
                "content_type": "text/plain",
                "status": "COMPLETED",
                "raw_items": raw_items
            }).execute()

            logger.info(f"[{idx}/3] Running chunking, classification, and embedding for {filename}...")
            await run_pipeline(file_id)
            logger.info(f"[{idx}/3] Successfully ingested {filename} (file_id: {file_id})!\n")
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    logger.info("All CUAD samples have been ingested into Supabase successfully!")

if __name__ == "__main__":
    asyncio.run(main())
