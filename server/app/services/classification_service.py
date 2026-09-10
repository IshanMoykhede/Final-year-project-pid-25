import os
import json
import time
import logging
from dotenv import load_dotenv
from groq import Groq
from app.core.supabase import connectSupa
from app.services.chunkBatching import create_batches
from app.schemas.ChunkAnlysis import BatchAnalysisResponse

logger = logging.getLogger(__name__)

# Force load environment variables from .env file
load_dotenv()

# Initialize Groq client
# Fallback to empty string to prevent crashing if not set
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """
You are a legal document analyzer. Your job is to read chunks of a legal document and return a JSON array.

For each chunk, you must provide:
1. classification_name: You MUST pick exactly ONE of these categories: "Work Culture", "Liability", "Termination", "Financial", "General". 
   (Note: If a chunk contains a table, classify it based on its content, e.g., a fee table is "Financial". If the chunk is just a logo or page number, use "General"). Do not invent new categories.
2. aliases: Nicknames for this clause (e.g., ["Section 4.2", "Termination Clause"]). Look at the headings.
3. direct_references: Other clauses mentioned inside this text (e.g., ["Article 5", "Annexure A"]).

CRITICAL: You are receiving a batch of multiple chunks. You MUST process EVERY SINGLE CHUNK. If I send you 41 chunks, your "results" array MUST contain exactly 41 items. DO NOT skip any chunks!

You MUST respond in strict JSON matching this schema:
{
  "results": [
    {
      "chunk_id": "uuid-here",
      "classification_name": "Liability",
      "aliases": ["Section 4", "Indemnification"],
      "direct_references": ["Clause 2(a)"]
    }
  ]
}
"""

def analyze_batch(batch_chunks: list) -> list:
    # Prepare the payload
    payload = []
    for chunk in batch_chunks:
        payload.append({
            "chunk_id": chunk["id"],
            "text": chunk["text"]
        })
        
    # Let the error bubble up to Swagger so we can see what went wrong!
    response = groq_client.chat.completions.create(
        # Using the 120b model as requested!
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze these chunks and return the JSON array: {json.dumps(payload)}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    json_response = json.loads(response.choices[0].message.content)
    # Validate with Pydantic to ensure perfect structure
    validated_data = BatchAnalysisResponse(**json_response)
    return validated_data.results

def process_document_classification(file_id: str):
    logger.info(f"Starting classification for document_id: {file_id}")
    supabase = connectSupa()
    
    # 1. Fetch chunks for this document
    result = (
        supabase
        .table("chunks")
        .select("*")
        .eq("document_id", file_id)
        .execute()
    )
    chunks = result.data
    
    if not chunks:
        logger.warning(f"No chunks found for document_id: {file_id}")
        return {"success": False, "message": "No chunks found."}
        
    # 2. Batch chunks using our batching engine
    # Groq free tier for 120b model has a strict 8,000 TPM limit!
    # We use 2000 to be extremely safe and leave room for output tokens.
    batches = create_batches(chunks, max_tokens_per_batch=2000)
    
    # 3. Process ALL batches
    all_results = []
    
    for i, batch in enumerate(batches):
        logger.info(f"[CLASSIFICATION_SERVICE] Sending Batch {i+1} of {len(batches)} to Groq (openai/gpt-oss-120b). Processing {len(batch)} chunks...")
        
        results = analyze_batch(batch)
        all_results.extend(results)
        
        # Avoid TPM rate limit (Tokens Per Minute)
        if i < len(batches) - 1:
            logger.info(f"[CLASSIFICATION_SERVICE] Batch {i+1} complete! Sleeping for 10 seconds to respect Groq rate limits...")
            time.sleep(10)
            
    # 4. Save results to Database
    logger.info(f"[CLASSIFICATION_SERVICE] All batches complete. Saving {len(all_results)} classified chunks to Supabase...")
    for res in all_results:
        try:
            # 4a. Find the classification ID in the database
            class_res = supabase.table("classifications").select("id").eq("name", res.classification_name).execute()
            
            # If we found it, use it. Otherwise, set it to None.
            if len(class_res.data) > 0:
                classification_id = class_res.data[0]["id"]
            else:
                classification_id = None
            
            # 4b. Update the chunk with the new data
            supabase.table("chunks").update({
                "classification_id": classification_id,
                "aliases": res.aliases
            }).eq("id", res.chunk_id).execute()
            
            # 4c. Insert direct references as AI_SUGGESTED
            for ref in res.direct_references:
                supabase.table("cross_references").insert({
                    "document_id": file_id,
                    "source_chunk_id": res.chunk_id,
                    "reference_text": ref,
                    "link_type": "AI_SUGGESTED"
                }).execute()
                
        except Exception as e:
            logger.error(f"Error saving chunk {res.chunk_id} to database: {e}")
            
    logger.info(f"Classification process complete for document_id: {file_id}")
    
    # ---------------------------------------------
    # PHASE 2: Automatically Resolve Cross-References
    # ---------------------------------------------
    from app.services.linking_service import resolve_cross_references
    linking_stats = resolve_cross_references(file_id)
    
    return {
        "success": True, 
        "total_chunks_processed": len(all_results),
        "linking_stats": linking_stats,
        "sample_result": all_results[0].model_dump() if all_results else None
    }