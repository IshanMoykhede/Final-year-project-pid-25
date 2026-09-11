from fastapi import APIRouter, HTTPException
import logging
from app.services.overview_service import generate_document_overview
from app.schemas.AnalyzerSchemas import OverviewResponse
from app.services.classification_service import process_document_classification

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analyze",
    tags=["Analysis Agent"]
)

@router.get("/overview/{file_id}", response_model=OverviewResponse)
async def get_document_overview(file_id: str, force_refresh: bool = False):
    """
    Phase 1: Deterministic Document Overview.
    Returns the document identity, breakdown of clauses, and a recommended reading roadmap.
    """
    try:
        result = await generate_document_overview(file_id, force_refresh)
        return result
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
