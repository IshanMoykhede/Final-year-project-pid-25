from fastapi import APIRouter, Depends, HTTPException
import logging

from app.schemas.chat import ChatRequest, ChatResponse
from app.dependencies.auth import get_current_user
from app.services.chat_service import answer_question
from app.core.supabase import connectSupa

import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/ask", response_model=ChatResponse)
async def ask_document_question(
    data: ChatRequest,
    current_user=Depends(get_current_user)
):
    supabase = connectSupa()
    
    # Verify user owns this document
    result = supabase.table("files").select("user_id").eq("id", data.document_id).maybe_single().execute()
    file = result.data if result else None
    
    if not file:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if file["user_id"] != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="You do not have access to this document")
        
    try:
        # Wrap CPU-bound and synchronous DB operations in a thread to prevent event loop blocking
        response = await asyncio.to_thread(
            answer_question, data.document_id, data.question, data.use_1hop_expansion
        )
        
        # Save chat to Supabase if requested
        if data.save_history:
            user_msg = {
                "document_id": data.document_id,
                "user_id": str(current_user["id"]),
                "role": "user",
                "content": data.question,
                "retrieved_chunk_ids": [],
                "is_expanded": False
            }
            
            # Extract chunk IDs from response
            chunk_ids = [c["chunk_id"] for c in response.get("primary_clauses", [])] + [c["chunk_id"] for c in response.get("expanded_clauses", [])]
            
            assistant_msg = {
                "document_id": data.document_id,
                "user_id": str(current_user["id"]),
                "role": "assistant",
                "content": response.get("answer", ""),
                "retrieved_chunk_ids": chunk_ids,
                "is_expanded": data.use_1hop_expansion
            }
            
            supabase.table("chat_messages").insert([user_msg, assistant_msg]).execute()
        
        return response
    except Exception as e:
        logger.exception(f"Chat failed for document {data.document_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/history")
async def get_chat_history(
    document_id: str,
    current_user=Depends(get_current_user)
):
    supabase = connectSupa()
    
    # Verify user owns this document
    result = supabase.table("files").select("user_id").eq("id", document_id).maybe_single().execute()
    file = result.data if result else None
    
    if not file:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if file["user_id"] != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="You do not have access to this document")
        
    try:
        history = supabase.table("chat_messages").select("*").eq("document_id", document_id).eq("user_id", str(current_user["id"])).order("created_at", desc=False).order("id", desc=False).execute()
        messages = history.data or []

        # Collect all chunk IDs referenced across assistant messages
        all_chunk_ids = set()
        for msg in messages:
            chunk_ids = msg.get("retrieved_chunk_ids") or []
            for cid in chunk_ids:
                if cid:
                    all_chunk_ids.add(cid)

        # Batch fetch chunk details
        chunks_map = {}
        if all_chunk_ids:
            chunk_res = supabase.table("chunks").select("id, chunk_no, text, aliases, bbox").in_("id", list(all_chunk_ids)).execute()
            for c in (chunk_res.data or []):
                chunks_map[c["id"]] = {
                    "chunk_id": c["id"],
                    "chunk_no": c.get("chunk_no"),
                    "text": c.get("text", ""),
                    "aliases": c.get("aliases") or [],
                    "bbox": c.get("bbox") or [],
                }

        # Attach resolved clauses to messages
        for msg in messages:
            msg_chunk_ids = msg.get("retrieved_chunk_ids") or []
            msg["clauses"] = [chunks_map[cid] for cid in msg_chunk_ids if cid in chunks_map]

        return {"messages": messages}
    except Exception as e:
        logger.exception(f"Failed to fetch chat history for document {document_id}")
        raise HTTPException(status_code=500, detail=str(e))
