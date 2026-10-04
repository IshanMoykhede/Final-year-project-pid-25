import logging
import asyncio
from datetime import datetime
from app.core.supabase import connectSupa
from app.services.overview_service import generate_document_overview
from app.Agents.Clause_Analyisis_Agent.graph import build_clause_agent_graph

logger = logging.getLogger(__name__)


async def initialize_analysis_session(file_id: str) -> dict:
    """
    Initializes an analysis session for a document and seeds placeholder
    rows in clause_analysis for all chunks if they don't already exist.
    """
    supabase = connectSupa()
    logger.info(f"[CLAUSE_SERVICE] Initializing analysis session for document: {file_id}")

    # 1. Fetch chunks for this document in chunk_no order
    chunks_res = (
        supabase
        .table("chunks")
        .select("id, chunk_no")
        .eq("document_id", file_id)
        .order("chunk_no", desc=False)
        .execute()
    )
    chunks = chunks_res.data
    if not chunks:
        raise ValueError(f"No chunks found for document {file_id}. Run preprocessing first.")

    total_clauses = len(chunks)

    # 2. Upsert analysis_sessions row
    session_payload = {
        "document_id": file_id,
        "total_clauses": total_clauses,
        "status": "INITIALIZED"
    }

    session_res = (
        supabase
        .table("analysis_sessions")
        .upsert(session_payload, on_conflict="document_id")
        .execute()
    )

    session_data = session_res.data[0] if session_res.data else {}
    session_id = session_data.get("id")

    # 3. Seed clause_analysis rows for any chunks that don't have one yet
    existing_analyses_res = (
        supabase
        .table("clause_analysis")
        .select("chunk_id")
        .eq("document_id", file_id)
        .execute()
    )
    existing_chunk_ids = {row["chunk_id"] for row in (existing_analyses_res.data or [])}

    new_rows = []
    for c in chunks:
        if c["id"] not in existing_chunk_ids:
            new_rows.append({
                "chunk_id": c["id"],
                "document_id": file_id,
                "session_id": session_id,
                "status": "PENDING"
            })

    if new_rows:
        logger.info(f"[CLAUSE_SERVICE] Seeding {len(new_rows)} pending clause_analysis rows...")
        supabase.table("clause_analysis").insert(new_rows).execute()

    return {
        "session_id": session_id,
        "document_id": file_id,
        "total_clauses": total_clauses,
        "status": "INITIALIZED"
    }


async def get_ordered_clauses_status(file_id: str) -> dict:
    """
    Returns all clauses in strict chunk_no serial order with their current
    analysis status to populate the Exam Portal Grid Window.
    """
    supabase = connectSupa()
    logger.info(f"[CLAUSE_SERVICE] Fetching ordered clause status for document: {file_id}")

    # 1. Fetch chunks ordered by chunk_no ASC
    chunks_res = (
        supabase
        .table("chunks")
        .select("id, chunk_no, text, aliases, classification_id")
        .eq("document_id", file_id)
        .order("chunk_no", desc=False)
        .execute()
    )
    chunks = chunks_res.data or []

    if not chunks:
        raise ValueError(f"No chunks found for document {file_id}.")

    # Fetch classifications for category mapping
    class_res = supabase.table("classifications").select("id, name").execute()
    class_map = {c["id"]: c["name"] for c in (class_res.data or [])}

    # 2. Fetch existing clause_analysis rows
    analyses_res = (
        supabase
        .table("clause_analysis")
        .select("*")
        .eq("document_id", file_id)
        .execute()
    )
    analysis_map = {a["chunk_id"]: a for a in (analyses_res.data or [])}

    # 3. Assemble serial order items
    clauses = []
    completed_count = 0
    in_progress_count = 0
    pending_count = 0

    for chunk in chunks:
        chunk_id = chunk["id"]
        analysis = analysis_map.get(chunk_id, {})
        status = analysis.get("status", "PENDING")

        if status == "COMPLETED":
            completed_count += 1
        elif status == "IN_PROGRESS":
            in_progress_count += 1
        else:
            pending_count += 1

        category_name = class_map.get(chunk.get("classification_id"), "General")

        clauses.append({
            "chunk_id": chunk_id,
            "chunk_no": chunk.get("chunk_no"),
            "category": category_name,
            "aliases": chunk.get("aliases") or [],
            "status": status,
            "risk_level": analysis.get("risk_level"),
            "has_analysis": status == "COMPLETED",
            "preview_text": (chunk.get("text") or "")[:120] + "..." if chunk.get("text") else ""
        })

    return {
        "document_id": file_id,
        "total_clauses": len(chunks),
        "completed": completed_count,
        "in_progress": in_progress_count,
        "pending": pending_count,
        "clauses": clauses
    }


async def analyze_clause_step(chunk_id: str, force_refresh: bool = False) -> dict:
    """
    Analyzes a single clause by chunk_id. Checks DB cache first;
    if cached, returns immediately. If pending, runs LangGraph Agent,
    stores output in DB, and returns result.
    """
    supabase = connectSupa()
    logger.info(f"[CLAUSE_SERVICE] Executing clause step for chunk_id: {chunk_id}")

    # 1. Fetch chunk info
    chunk_res = (
        supabase
        .table("chunks")
        .select("*")
        .eq("id", chunk_id)
        .single()
        .execute()
    )
    chunk = chunk_res.data
    if not chunk:
        raise ValueError(f"Chunk {chunk_id} not found.")

    file_id = chunk["document_id"]

    # 2. Check DB Cache
    existing_res = (
        supabase
        .table("clause_analysis")
        .select("*")
        .eq("chunk_id", chunk_id)
        .execute()
    )
    existing = existing_res.data[0] if existing_res.data else None

    if existing and existing.get("status") == "COMPLETED" and not force_refresh:
        logger.info(f"[CLAUSE_SERVICE] Cache Hit! Returning stored analysis for chunk {chunk_id}")
        return {
            "chunk_id": chunk_id,
            "document_id": file_id,
            "chunk_no": chunk.get("chunk_no"),
            "status": "COMPLETED",
            "cached": True,
            "analysis": {
                "explanation": existing.get("explanation"),
                "entities_involved": existing.get("entities_involved"),
                "real_world_examples": existing.get("real_world_examples"),
                "risk_level": existing.get("risk_level"),
                "risk_analysis": existing.get("risk_analysis"),
                "negotiation_advice": existing.get("negotiation_advice"),
                "faqs": existing.get("faqs"),
                "document_citations": existing.get("document_citations"),
                "web_citations": existing.get("web_citations")
            }
        }

    # 3. Mark status as IN_PROGRESS
    if existing:
        supabase.table("clause_analysis").update({"status": "IN_PROGRESS"}).eq("chunk_id", chunk_id).execute()
    else:
        supabase.table("clause_analysis").insert({
            "chunk_id": chunk_id,
            "document_id": file_id,
            "status": "IN_PROGRESS"
        }).execute()

    # 4. Prepare Context for LangGraph Agent
    class_name = "General"
    if chunk.get("classification_id"):
        c_res = supabase.table("classifications").select("name").eq("id", chunk["classification_id"]).execute()
        if c_res.data:
            class_name = c_res.data[0]["name"]

    # Fetch document overview for macro context
    overview = await generate_document_overview(file_id)
    overview_summary = overview.get("summary", "")

    # Fetch pre-linked cross-references
    refs_res = (
        supabase
        .table("cross_references")
        .select("*")
        .eq("source_chunk_id", chunk_id)
        .execute()
    )
    direct_references = refs_res.data or []

    initial_state = {
        "chunk_id": chunk_id,
        "document_id": file_id,
        "clause_type": class_name,
        "original_text": chunk.get("text", ""),
        "document_overview": overview_summary,
        "direct_references": direct_references,
        "rag_results": [],
        "web_results": [],
        "messages": [],
        "tool_call_count": 0,
        "verification_retry_count": 0,
        "errors": []
    }

    # 5. Invoke LangGraph Agent
    logger.info(f"[CLAUSE_SERVICE] Invoking LangGraph Agent for chunk {chunk_id}...")
    app_graph = build_clause_agent_graph()
    final_state = await asyncio.to_thread(app_graph.invoke, initial_state)

    final_analysis = final_state.get("final_analysis", {})

    # 6. Save Analysis to DB
    update_payload = {
        "document_id": file_id,
        "status": "COMPLETED",
        "explanation": final_analysis.get("explanation"),
        "entities_involved": final_analysis.get("entities_involved"),
        "real_world_examples": final_analysis.get("real_world_examples"),
        "risk_level": final_analysis.get("risk_level", "LOW"),
        "risk_analysis": final_analysis.get("risk_analysis"),
        "negotiation_advice": final_analysis.get("negotiation_advice"),
        "faqs": final_analysis.get("faqs"),
        "document_citations": final_analysis.get("document_citations"),
        "web_citations": final_analysis.get("web_citations"),
        "completed_at": datetime.utcnow().isoformat()
    }

    supabase.table("clause_analysis").update(update_payload).eq("chunk_id", chunk_id).execute()

    # Update session counters
    try:
        session_res = supabase.table("analysis_sessions").select("id, completed").eq("document_id", file_id).execute()
        if session_res.data:
            s_id = session_res.data[0]["id"]
            current_completed = session_res.data[0].get("completed", 0)
            supabase.table("analysis_sessions").update({"completed": current_completed + 1}).eq("id", s_id).execute()
    except Exception as e:
        logger.warning(f"[CLAUSE_SERVICE] Failed to update session counter: {e}")

    logger.info(f"[CLAUSE_SERVICE] Successfully analyzed and saved chunk {chunk_id}")

    return {
        "chunk_id": chunk_id,
        "document_id": file_id,
        "chunk_no": chunk.get("chunk_no"),
        "status": "COMPLETED",
        "cached": False,
        "analysis": final_analysis
    }
