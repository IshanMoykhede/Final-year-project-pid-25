from fastapi import APIRouter, Depends, HTTPException
import logging

from app.schemas.chat import ChatRequest, ChatResponse
from app.dependencies.auth import get_current_user
from app.services.chat_service import answer_question
from app.core.supabase import connectSupa

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
        response = answer_question(data.document_id, data.question, data.use_1hop_expansion)
        return response
    except Exception as e:
        logger.exception(f"Chat failed for document {data.document_id}")
        raise HTTPException(status_code=500, detail=str(e))
