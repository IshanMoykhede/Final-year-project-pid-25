from fastapi import APIRouter, HTTPException, Depends
import logging
from app.services.overview_service import generate_document_overview
from app.schemas.AnalyzerSchemas import OverviewResponse, DocumentRiskResponse, ClauseAnalysisRequest
from app.services.classification_service import process_document_classification
from app.services.risk_service import analyze_document_risks
from app.dependencies.auth import verify_file_ownership
from app.Agents.Clause_Analyisis_Agent.graph import build_clause_agent_graph
from app.Agents.Clause_Analyisis_Agent.tools import search_document, search_market_standards

from app.services.clause_analysis_service import (
    initialize_analysis_session,
    get_ordered_clauses_status,
    analyze_clause_step
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analyze",
    tags=["Analysis Agent"]
)

@router.get("/overview/{file_id}", response_model=OverviewResponse)
async def get_document_overview(
    file_id: str,
    force_refresh: bool = False,
    file: dict = Depends(verify_file_ownership)
):
    """
    Phase 1: Deterministic Document Overview.
    Returns the document identity, breakdown of clauses, and a recommended reading roadmap.
    Enforces user ownership via verify_file_ownership.
    """
    try:
        result = await generate_document_overview(file["id"], force_refresh)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to generate overview")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/{file_id}", response_model=DocumentRiskResponse)
async def get_document_risks(
    file_id: str,
    force_refresh: bool = False,
    file: dict = Depends(verify_file_ownership)
):
    """
    Phase 2: Deep Document Risk Analysis.
    (Temporarily disabled to conserve LLM tokens)
    """
    return DocumentRiskResponse(
        high_risks=[],
        medium_risks=[],
        low_risks=[],
        total_risks=0
    )
    # try:
    #     result = await analyze_document_risks(file["id"], force_refresh)
    #     return result
    # except ValueError as ve:
    #     raise HTTPException(status_code=404, detail=str(ve))
    # except Exception as e:
    #     logger.exception("Failed to analyze document risks")
    #     raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/initialize/{file_id}")
async def initialize_session(file_id: str):
    """
    Initializes an Exam Portal analysis session and seeds clause placeholders.
    """
    try:
        result = await initialize_analysis_session(file_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to initialize analysis session")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clause/ordered-list/{file_id}")
async def get_ordered_clauses(file_id: str):
    """
    Returns all document clauses in serial chunk_no order with their status
    to render the Exam Portal Grid Window.
    """
    try:
        result = await get_ordered_clauses_status(file_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to fetch ordered clauses")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clause/step/{chunk_id}")
async def execute_clause_step(chunk_id: str, force_refresh: bool = False):
    """
    Analyzes a single clause in serial order. Checks DB cache first;
    returns cached result instantly if available, or invokes the Agent.
    """
    try:
        result = await analyze_clause_step(chunk_id, force_refresh)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception(f"Failed to analyze clause step for chunk {chunk_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clause/{chunk_id}")
async def analyze_clause(chunk_id: str, request: ClauseAnalysisRequest):
    """
    Phase 3: Deep Legal Analysis of a single clause.
    The frontend passes the state directly to the Agent Graph to execute the 120b model.
    """
    try:
        # We run the graph in a thread to prevent blocking FastAPI's async event loop
        import asyncio
        
        # Build the LangGraph application
        app_graph = build_clause_agent_graph()
        
        # Prepare the state dictionary from the frontend's request
        initial_state = {
            "chunk_id": chunk_id,
            "document_id": request.document_id,
            "clause_type": request.clause_type,
            "original_text": request.original_text,
            "document_overview": request.document_overview,
            "direct_references": request.direct_references,
            "rag_results": request.rag_results,
            "web_results": request.web_results,
            "messages": [], # Reset messages for a fresh run
            "tool_call_count": 0,
            "verification_retry_count": 0,
            "errors": []
        }
        
        # Invoke the graph
        final_state = await asyncio.to_thread(app_graph.invoke, initial_state)
        
        # Return the final JSON analysis directly to the frontend
        return final_state.get("final_analysis", {})
        
    except Exception as e:
        logger.exception("Failed to analyze clause via Agent Graph")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-classification/{file_id}")
async def test_dynamic_classification(
    file_id: str,
    file: dict = Depends(verify_file_ownership)
):
    """
    Testing endpoint: Reruns the Phase 0 Dynamic Classification (Discovery + Batching) 
    on an already chunked document, without needing to restart OCR/Chunking.
    Enforces user ownership via verify_file_ownership.
    """
    try:
        # Since it's synchronous, we run it in a thread pool so it doesn't block FastAPI
        import asyncio
        result = await asyncio.to_thread(process_document_classification, file["id"])
        return result
    except Exception as e:
        logger.exception("Failed to run classification test")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-rag/{file_id}")
async def test_rag_retrieval(file_id: str, query: str):
    """
    Testing endpoint: Tests the RAG (Semantic Search) tool directly.
    Make sure you have run the 'match_chunks' SQL in Supabase first!
    """
    try:
        # The tool expects (query, document_id)
        result = search_document.invoke({"query": query, "document_id": file_id})
        return {"query": query, "result": result}
    except Exception as e:
        logger.exception("Failed to test RAG")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-web-search")
async def test_web_search(query: str):
    """
    Testing endpoint: Tests the Tavily Web Search tool directly.
    """
    try:
        result = search_market_standards.invoke({"query": query})
        return {"query": query, "result": result}
    except Exception as e:
        logger.exception("Failed to test Web Search")
        raise HTTPException(status_code=500, detail=str(e))
