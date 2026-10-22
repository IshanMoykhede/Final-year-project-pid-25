import logging
import time
import asyncio
from fastapi import APIRouter, HTTPException, Depends

from app.core.supabase import connectSupa
from app.dependencies.auth import get_current_user
from app.services.flash_analysis_service import generate_flash_analysis

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/flash-analysis",
    tags=["Flash Analysis"]
)


@router.post("/{document_id}")
async def analyze_document_flash(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Flash Analysis — produces a complete, structured legal report
    for an entire document in a single LLM call.

    Steps:
      1. Validate document exists and belongs to the current user.
      2. Check the document has been fully processed (status = COMPLETED).
      3. Fetch all chunks in chunk_no order.
      4. Combine chunks into one ordered document context string.
      5. Call the Flash Analysis service (gpt-oss-120b).
      6. Return the structured JSON report.
    """
    request_start = time.time()
    user_id = current_user.get("id")

    logger.info(
        f"[FLASH_ANALYSIS] Request received — document_id={document_id}, user_id={user_id}"
    )

    supabase = connectSupa()
    if not supabase:
        logger.error("[FLASH_ANALYSIS] Supabase connection failed.")
        raise HTTPException(status_code=500, detail="Database connection failed.")

    # ── 1. Fetch document and verify ownership ───────────────────────────
    try:
        file_res = (
            supabase
            .table("files")
            .select("id, user_id, file_name, status")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except Exception as e:
        logger.error(f"[FLASH_ANALYSIS] DB error while fetching document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching document.")

    if not file_res.data:
        logger.warning(f"[FLASH_ANALYSIS] Document {document_id} not found.")
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = file_res.data

    # Ownership check — never expose another user's document
    if doc.get("user_id") != user_id:
        logger.warning(
            f"[FLASH_ANALYSIS] Forbidden — user {user_id} tried to access document {document_id} "
            f"owned by {doc.get('user_id')}."
        )
        raise HTTPException(status_code=403, detail="You do not have access to this document.")

    # ── 2. Check processing status ───────────────────────────────────────
    doc_status = doc.get("status", "")
    if doc_status != "COMPLETED":
        logger.warning(
            f"[FLASH_ANALYSIS] Document {document_id} is not fully processed. "
            f"Current status: {doc_status}"
        )
        raise HTTPException(
            status_code=422,
            detail=f"Document preprocessing is not complete. Current status: '{doc_status}'. "
                   "Please wait for processing to finish before running Flash Analysis."
        )

    # ── 3. Fetch all chunks in original document order ───────────────────
    logger.info(f"[FLASH_ANALYSIS] Fetching chunks for document {document_id}...")

    try:
        chunks_res = (
            supabase
            .table("chunks")
            .select("chunk_no, text")
            .eq("document_id", document_id)
            .order("chunk_no", desc=False)
            .execute()
        )
    except Exception as e:
        logger.error(f"[FLASH_ANALYSIS] DB error while fetching chunks for {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching document chunks.")

    chunks = chunks_res.data or []
    chunk_count = len(chunks)

    logger.info(f"[FLASH_ANALYSIS] Retrieved {chunk_count} chunks for document {document_id}.")

    if chunk_count == 0:
        logger.warning(f"[FLASH_ANALYSIS] No chunks found for document {document_id}.")
        raise HTTPException(
            status_code=422,
            detail="No processed content found for this document. "
                   "Please ensure the document has been fully preprocessed."
        )

    # ── 4. Combine chunks into one ordered document context string ────────
    # Each chunk is separated by a blank line to preserve readability for the LLM.
    document_context = "\n\n".join(
        chunk["text"] for chunk in chunks if chunk.get("text")
    )

    logger.info(
        f"[FLASH_ANALYSIS] Document context built — "
        f"{len(document_context)} characters from {chunk_count} chunks."
    )

    # ── 5. Call the Flash Analysis service ───────────────────────────────
    try:
        logger.info(f"[FLASH_ANALYSIS] Starting LLM call for document {document_id}...")

        # generate_flash_analysis is synchronous (Groq client is sync);
        # run in a thread so we don't block FastAPI's async event loop.
        report = await asyncio.to_thread(
            generate_flash_analysis, document_context, document_id
        )

    except ValueError as ve:
        # Context-limit exceeded or other validation errors from the service
        logger.warning(f"[FLASH_ANALYSIS] Validation error for document {document_id}: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))

    except Exception as e:
        logger.exception(
            f"[FLASH_ANALYSIS] LLM error while analyzing document {document_id}: {e}"
        )
        raise HTTPException(
            status_code=502,
            detail="Flash Analysis failed due to an upstream LLM error. Please try again."
        )

    # ── 6. Return result ─────────────────────────────────────────────────
    total_duration = round(time.time() - request_start, 2)
    logger.info(
        f"[FLASH_ANALYSIS] Report generated successfully for document {document_id} "
        f"in {total_duration}s total."
    )

    return {
        "success": True,
        "document_id": document_id,
        "file_name": doc.get("file_name"),
        "chunk_count": chunk_count,
        "report": report
    }
