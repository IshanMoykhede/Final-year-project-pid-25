import logging
import json
from app.core.supabase import connectSupa
from groq import Groq
from app.schemas.AnalyzerSchemas import DocumentIdentity, RoadmapResult, OverviewResponse, CategoryCount
import os

logger = logging.getLogger(__name__)

async def generate_document_overview(file_id: str, force_refresh: bool = False) -> dict:
    """
    Generates a deterministic overview of the document (Phase 1).
    Checks cache first. If not cached, executes 2 fast LLM calls.
    """
    supabase = connectSupa()
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    
    # 1. Check Cache
    if not force_refresh:
        file_record = supabase.table("files").select("overview_cache").eq("id", file_id).execute()
        if not file_record.data:
            raise ValueError(f"File {file_id} not found.")
            
        cached = file_record.data[0].get("overview_cache")
        if cached:
            logger.info(f"[OVERVIEW_SERVICE] Returning cached overview for {file_id}")
            return cached

    logger.info(f"[OVERVIEW_SERVICE] No cache found. Generating deterministic overview for {file_id}...")

    # 2. SQL Query -> Count chunks per category (No LLM)
    # Get all chunks for the document with their classification names
    # Because Supabase Python doesn't support complex aggregations easily, we'll fetch classifications and map
    chunks_res = supabase.table("chunks").select("id, text, classification_id").eq("document_id", file_id).execute()
    chunks = chunks_res.data
    
    if not chunks:
        raise ValueError("No chunks found. Is the document preprocessed?")

    class_res = supabase.table("classifications").select("id, name").execute()
    class_map = {c["id"]: c["name"] for c in class_res.data}

    # Count them
    breakdown_counts = {}
    total_clauses = len(chunks)
    
    for c in chunks:
        name = class_map.get(c.get("classification_id"), "Unclassified")
        breakdown_counts[name] = breakdown_counts.get(name, 0) + 1

    breakdown = [{"category": k, "count": v} for k, v in breakdown_counts.items()]

    # 3. First 5 chunks (len > 200) -> one LLM call -> Document Identity
    # Filter out TOC / short headers
    valid_chunks = [c["text"] for c in chunks if c.get("text") and len(c["text"]) > 200]
    top_chunks_text = "\n\n---\n\n".join(valid_chunks[:5])

    logger.info("[OVERVIEW_SERVICE] Calling LLM (Call 1) for Document Identity...")
    identity_completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",  # We can use the fast/cheap model for this simple task
        messages=[
            {"role": "system", "content": "You are a legal document analyzer. Read the preamble/top chunks of this document and return a strict JSON according to the schema. Make sure to accurately extract the exact party names, jurisdiction, and explicitly map the document type to the provided enum."},
            {"role": "user", "content": f"Document Text:\n{top_chunks_text}"}
        ],
        response_format={"type": "json_schema", "json_schema": {"name": "DocumentIdentity", "schema": DocumentIdentity.model_json_schema()}},
        temperature=0.1
    )
    
    identity_res = json.loads(identity_completion.choices[0].message.content)
    document_type = identity_res.get("document_type", "Unknown Document")
    plain_summary = identity_res.get("plain_summary", "A legal document.")
    parties = identity_res.get("parties", [])
    jurisdiction = identity_res.get("jurisdiction", "Unknown")

    # 4. Document Type + Breakdown -> one LLM call -> Recommended Roadmap
    logger.info("[OVERVIEW_SERVICE] Calling LLM (Call 2) for Roadmap...")
    roadmap_prompt = f"""Document Type: {document_type}
Clause Breakdown: {json.dumps(breakdown)}

Based ONLY on the Document Type and the categories present in the Clause Breakdown, generate an ordered array roadmap of the categories.
CRITICAL INSTRUCTION: Order the roadmap by importance to a non-lawyer reviewing the document, NOT by clause count. 
Categories with fewer clauses can still be higher priority if they carry more legal risk.
For example, for a Lease, the ideal order is often [Financial, Termination, Liability, General].
For an NDA, it might be [Liability, Confidentiality, Termination, General].
Return strict JSON."""
    
    roadmap_completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a UX guide for a legal tech app. Return strict JSON according to the schema."},
            {"role": "user", "content": roadmap_prompt}
        ],
        response_format={"type": "json_schema", "json_schema": {"name": "RoadmapResult", "schema": RoadmapResult.model_json_schema()}},
        temperature=0.1
    )
    
    roadmap_res = json.loads(roadmap_completion.choices[0].message.content)
    roadmap_array = roadmap_res.get("recommended_roadmap", [])
    starting_point = roadmap_res.get("recommended_starting_point", "")
    reasoning = roadmap_res.get("reasoning", "")

    # 5. Assemble and Cache
    final_result = {
        "document_type": document_type,
        "summary": plain_summary,
        "parties": parties,
        "jurisdiction": jurisdiction,
        "total_clauses": total_clauses,
        "breakdown": breakdown,
        "recommended_roadmap": roadmap_array,
        "recommended_starting_point": starting_point,
        "reasoning": reasoning
    }

    logger.info(f"[OVERVIEW_SERVICE] Overview generated successfully. Caching...")
    try:
        supabase.table("files").update({"overview_cache": final_result}).eq("id", file_id).execute()
    except Exception as e:
        logger.error(f"[OVERVIEW_SERVICE] Failed to cache to DB. Did you add the 'overview_cache' column? Error: {e}")
        # We don't raise here, so the user can still test the route even if DB isn't updated yet.

    return final_result
