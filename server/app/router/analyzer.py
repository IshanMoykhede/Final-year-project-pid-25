import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from app.core.supabase import connectSupa
from app.dependencies.auth import get_current_user
from app.services.overview_service import generate_document_overview
from app.schemas.AnalyzerSchemas import OverviewResponse
from app.services.classification_service import process_document_classification
from app.services.risk_service import analyze_document_risk
from app.schemas.risk import RiskAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analyze",
    tags=["Analysis Agent"]
)

@router.get("/overview/{file_id}", response_model=OverviewResponse)
async def get_document_overview(
    file_id: str,
    force_refresh: bool = False,
    current_user=Depends(get_current_user),
):
    """
    Phase 1: Deterministic Document Overview.
    Returns the document identity, breakdown of clauses, and a recommended reading roadmap.
    """
    try:
        supabase = connectSupa()
        file_result = supabase.table("files").select("user_id").eq("id", file_id).maybe_single().execute()
        file = file_result.data if file_result else None
        if not file:
            raise HTTPException(status_code=404, detail="Document not found")
        if file["user_id"] != str(current_user["id"]):
            raise HTTPException(status_code=403, detail="You do not have access to this document")

        result = await generate_document_overview(file_id, force_refresh)
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to generate overview")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-classification/{file_id}")
async def test_dynamic_classification(file_id: str):
    """
    Testing endpoint: Reruns the Phase 0 Dynamic Classification (Discovery + Batching) 
    on an already chunked document, without needing to restart OCR/Chunking.
    """
    try:
        # Since it's synchronous, we run it in a thread pool so it doesn't block FastAPI
        import asyncio
        result = await asyncio.to_thread(process_document_classification, file_id)
        return result
    except Exception as e:
        logger.exception("Failed to run classification test")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{file_id}", response_model=RiskAnalysisResponse)
async def get_document_risk(
    file_id: str,
    force_refresh: bool = False,
    current_user=Depends(get_current_user),
):
    try:
        supabase = connectSupa()
        file_result = supabase.table("files").select("user_id").eq("id", file_id).maybe_single().execute()
        file = file_result.data if file_result else None
        if not file:
            raise HTTPException(status_code=404, detail="Document not found")
        if file["user_id"] != str(current_user["id"]):
            raise HTTPException(status_code=403, detail="You do not have access to this document")
        return await asyncio.to_thread(analyze_document_risk, file_id, force_refresh)
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        logger.exception("Failed to generate risk analysis")
        raise HTTPException(status_code=500, detail=str(error))
