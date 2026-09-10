import asyncio
import json
import logging
from app.core.supabase import connectSupa
from app.services.ocr_service import process_document
from app.services.chunking_service import chunk_document
from app.services.classification_service import process_document_classification

logger = logging.getLogger(__name__)

def create_sse_event(step: str, status: str, message: str = ""):
    """Formats a Server-Sent Event string and logs it to the terminal"""
    
    # 1. Log to the terminal
    if status == "error":
        logger.error(f"[PIPELINE - {step}] {message}")
    elif step == "HEARTBEAT":
        # Keep heartbeats on the terminal so you know it's alive!
        logger.info(f"[PIPELINE - {step}] {message}")
    else:
        logger.info(f"[PIPELINE - {step}] {status.upper()}: {message}")
        
    # 2. Format for SSE frontend streaming
    data = json.dumps({"step": step, "status": status, "message": message})
    return f"data: {data}\n\n"

async def run_with_heartbeat(func, *args):
    """
    Runs a long synchronous function in a background thread, 
    yielding heartbeats every 5 seconds to keep the SSE connection alive.
    """
    task = asyncio.create_task(asyncio.to_thread(func, *args))
    
    while not task.done():
        yield create_sse_event("HEARTBEAT", "processing", "Still working...")
        await asyncio.sleep(5)
        
    # Check if task raised an exception and return its result
    result = task.result()
    # We must yield a dummy value so this is technically an async generator
    # but the calling function consumes it.
    yield ("RESULT", result)

async def preprocess_document_sse(file_id: str):
    """
    The orchestrator pipeline using Server-Sent Events (SSE).
    Uses the Supabase Database as a Native Checkpointer for fallbacks!
    """
    supabase = connectSupa()
    
    try:
        # Check current status in DB
        result = supabase.table("files").select("status").eq("id", file_id).execute()
        if not result.data:
            yield create_sse_event("INIT", "error", "File not found")
            return
            
        current_status = result.data[0].get("status", "uploaded")
        
        # ---------------------------------------------------------
        # 1. OCR Step
        # ---------------------------------------------------------
        if current_status in ["uploaded", "OCR_FAILED"]:
            yield create_sse_event("OCR", "processing", "Starting OCR with LlamaParse...")
            supabase.table("files").update({"status": "OCR_IN_PROGRESS"}).eq("id", file_id).execute()
            
            try:
                # Run with heartbeats!
                async for event in run_with_heartbeat(process_document, file_id):
                    if isinstance(event, tuple): pass # Result tuple, ignore
                    else: yield event
                
                supabase.table("files").update({"status": "OCR_COMPLETED"}).eq("id", file_id).execute()
                yield create_sse_event("OCR", "completed", "OCR successful")
            except Exception as e:
                supabase.table("files").update({"status": "OCR_FAILED"}).eq("id", file_id).execute()
                yield create_sse_event("OCR", "error", str(e))
                return
                
        # ---------------------------------------------------------
        # 2. Chunking Step
        # ---------------------------------------------------------
        current_status = supabase.table("files").select("status").eq("id", file_id).execute().data[0].get("status")
        
        if current_status in ["OCR_COMPLETED", "CHUNKING_FAILED"]:
            yield create_sse_event("CHUNKING", "processing", "Chunking document text...")
            supabase.table("files").update({"status": "CHUNKING_IN_PROGRESS"}).eq("id", file_id).execute()
            
            try:
                async for event in run_with_heartbeat(chunk_document, file_id):
                    if isinstance(event, tuple): pass
                    else: yield event
                    
                supabase.table("files").update({"status": "CHUNKING_COMPLETED"}).eq("id", file_id).execute()
                yield create_sse_event("CHUNKING", "completed", "Chunking successful")
            except Exception as e:
                supabase.table("files").update({"status": "CHUNKING_FAILED"}).eq("id", file_id).execute()
                yield create_sse_event("CHUNKING", "error", str(e))
                return

        # ---------------------------------------------------------
        # 3. Classification & Linking Step
        # ---------------------------------------------------------
        current_status = supabase.table("files").select("status").eq("id", file_id).execute().data[0].get("status")
        
        if current_status in ["CHUNKING_COMPLETED", "CLASSIFICATION_FAILED"]:
            yield create_sse_event("CLASSIFICATION", "processing", "Classifying chunks & resolving links...")
            supabase.table("files").update({"status": "CLASSIFICATION_IN_PROGRESS"}).eq("id", file_id).execute()
            
            try:
                async for event in run_with_heartbeat(process_document_classification, file_id):
                    if isinstance(event, tuple): pass
                    else: yield event
                    
                supabase.table("files").update({"status": "CLASSIFICATION_COMPLETED"}).eq("id", file_id).execute()
                yield create_sse_event("CLASSIFICATION", "completed", "Classification and Linking successful")
            except Exception as e:
                supabase.table("files").update({"status": "CLASSIFICATION_FAILED"}).eq("id", file_id).execute()
                yield create_sse_event("CLASSIFICATION", "error", str(e))
                return


        # ---------------------------------------------------------
        # 4. Vector Embedding Step
        # ---------------------------------------------------------
        current_status = supabase.table("files").select("status").eq("id", file_id).execute().data[0].get("status")
        
        if current_status in ["CLASSIFICATION_COMPLETED", "EMBEDDING_FAILED"]:
            yield create_sse_event("EMBEDDING", "processing", "Generating semantic vectors for Agentic RAG...")
            supabase.table("files").update({"status": "EMBEDDING_IN_PROGRESS"}).eq("id", file_id).execute()
            
            try:
                from app.services.embedding_service import generate_embeddings
                async for event in run_with_heartbeat(generate_embeddings, file_id):
                    if isinstance(event, tuple): pass
                    else: yield event
                    
                supabase.table("files").update({"status": "COMPLETED"}).eq("id", file_id).execute()
                yield create_sse_event("EMBEDDING", "completed", "Semantic vectors successfully generated")
            except Exception as e:
                supabase.table("files").update({"status": "EMBEDDING_FAILED"}).eq("id", file_id).execute()
                yield create_sse_event("EMBEDDING", "error", str(e))
                return

        # If it reached here, everything is done!
        current_status = supabase.table("files").select("status").eq("id", file_id).execute().data[0].get("status")
        if current_status == "COMPLETED":
            yield create_sse_event("PIPELINE", "completed", "All preprocessing steps finished successfully!")
        else:
            yield create_sse_event("PIPELINE", "completed", f"Pipeline finished with status: {current_status}")

    except Exception as e:
        logger.exception("Pipeline failed")
        yield create_sse_event("PIPELINE", "error", str(e))
