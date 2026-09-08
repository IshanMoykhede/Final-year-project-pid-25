from app.core.supabase import connectSupa
import logging

logger = logging.getLogger(__name__)

# If a chunk grows beyond this many characters,
# force-save it and start a new one.
# 10000 chars is a very large chunk, good for keeping long clauses together.
MAX_CHUNK_SIZE = 10000


def chunk_document(file_id: str):
    logger.info(f"Starting chunking process for document_id: {file_id}")
    supabase = connectSupa()

    # -----------------------------------------
    # STEP 1: Fetch raw_items JSON from files table
    # -----------------------------------------

    result = (
        supabase
        .table("files")
        .select("raw_items")
        .eq("id", file_id)
        .single()
        .execute()
    )

    file = result.data

    if not file:
        raise ValueError("File not found")

    raw_items = file.get("raw_items")

    if not raw_items:
        raise ValueError("No parsed data found. Run OCR first.")

    # -----------------------------------------
    # STEP 2: Flatten all items from all pages
    #         into one big list so we can loop
    #         through them in order
    # -----------------------------------------

    all_items = []

    # raw_items can be a dict with "pages" key or a list of pages
    if isinstance(raw_items, dict):
        pages = raw_items.get("pages", [])
    elif isinstance(raw_items, list):
        pages = raw_items
    else:
        pages = []

    for page in pages:
        page_number = page.get("page_number", 0)
        items = page.get("items", [])

        for item in items:
            # Tag each item with its page number so we can track it
            item["_page_number"] = page_number
            all_items.append(item)

    # -----------------------------------------
    # STEP 3: Walk through all items and chunk
    #         heading-to-heading
    # -----------------------------------------

    chunks = []
    current_text = ""
    current_bboxes = []
    chunk_no = 0

    for item in all_items:
        item_type = item.get("type", "")

        # ---- HEADING FOUND: save previous chunk, start new one ----
        if item_type == "heading":

            # Save the previous chunk if it has any text
            if current_text.strip():
                chunk_no = chunk_no + 1
                chunks.append({
                    "document_id": file_id,
                    "classification_id": None,
                    "chunk_no": chunk_no,
                    "text": current_text.strip(),
                    "bbox": current_bboxes if len(current_bboxes) > 0 else None
                })

            # Start a brand new chunk with this heading's text
            current_text = item.get("md", "") + "\n"
            current_bboxes = []

            # Grab bbox from heading if it exists
            if item.get("bbox"):
                for box in item.get("bbox"):
                    box["page_number"] = item.get("_page_number")
                    current_bboxes.append(box)

        # ---- NOT A HEADING: append to current chunk ----
        else:
            md_text = item.get("md", "")

            if md_text:
                current_text = current_text + md_text + "\n"

            # Grab bbox if it exists
            if item.get("bbox"):
                for box in item.get("bbox"):
                    box["page_number"] = item.get("_page_number")
                    current_bboxes.append(box)

            # ---- FALLBACK: if chunk is too big, save it now ----
            if len(current_text) > MAX_CHUNK_SIZE:
                chunk_no = chunk_no + 1
                chunks.append({
                    "document_id": file_id,
                    "classification_id": None,
                    "chunk_no": chunk_no,
                    "text": current_text.strip(),
                    "bbox": current_bboxes if len(current_bboxes) > 0 else None
                })
                current_text = ""
                current_bboxes = []

    # -----------------------------------------
    # STEP 4: Don't forget the LAST chunk!
    # -----------------------------------------

    if current_text.strip():
        chunk_no = chunk_no + 1
        chunks.append({
            "document_id": file_id,
            "classification_id": None,
            "chunk_no": chunk_no,
            "text": current_text.strip(),
            "bbox": current_bboxes if len(current_bboxes) > 0 else None
        })

    # -----------------------------------------
    # STEP 5: Save all chunks to database
    # -----------------------------------------

    if len(chunks) > 0:
        logger.info(f"Generated {len(chunks)} chunks for document_id: {file_id}. Storing to database...")

        try:
            # First, delete old chunks for this document (in case we re-run)
            (
                supabase
                .table("chunks")
                .delete()
                .eq("document_id", file_id)
                .execute()
            )

            # Then insert all new chunks
            (
                supabase
                .table("chunks")
                .insert(chunks)
                .execute()
            )
            logger.info(f"Successfully stored {len(chunks)} chunks in database for document_id: {file_id}")
            
        except Exception as e:
            logger.exception(f"Chunking process failed to save database for document_id: {file_id}")
            raise

    return chunks
