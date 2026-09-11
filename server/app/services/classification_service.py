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

def get_system_prompt(categories: list) -> str:
    categories_str = ", ".join([f'"{c}"' for c in categories])
    return f"""
You are a legal document analyzer. Your job is to read chunks of a legal document and return a JSON array.

For each chunk, you must provide:
1. classification_name: You MUST pick exactly ONE of these categories: {categories_str}. 
   (Note: If a chunk contains a table, classify it based on its content, e.g., a fee table is "Financial". If the chunk is just a logo or page number, use "General"). Do not invent new categories.
2. aliases: Nicknames for this clause (e.g., ["Section 4.2", "Termination Clause"]). Look at the headings.
3. direct_references: Other clauses mentioned inside this text (e.g., ["Article 5", "Annexure A"]).

CRITICAL: You are receiving a batch of multiple chunks. You MUST process EVERY SINGLE CHUNK. If I send you 41 chunks, your "results" array MUST contain exactly 41 items. DO NOT skip any chunks!

You MUST respond in strict JSON matching this schema:
{{
  "results": [
    {{
      "chunk_id": "uuid-here",
      "classification_name": "picked-category",
      "aliases": ["Section 4", "Indemnification"],
      "direct_references": ["Clause 2(a)"]
    }}
  ]
}}
"""

def discover_categories(chunks: list, supabase) -> list:
    logger.info("[CLASSIFICATION_SERVICE] Starting Dynamic Category Discovery with Rolling Batches...")
    
    # Use our safe batching engine to avoid token limits
    # 3500 tokens is safe since we only expect a tiny JSON output
    batches = create_batches(chunks, max_tokens_per_batch=3500)
    
    # To avoid taking 20 minutes on massive documents, we'll sample up to 4 batches 
    # (Beginning, early-middle, late-middle, end) to get a full picture of the document architecture.
    if len(batches) > 4:
        step = len(batches) // 4
        sampled_batches = [batches[0], batches[step], batches[step*2], batches[-1]]
    else:
        sampled_batches = batches

    current_categories = ["General"]
    
    for i, batch in enumerate(sampled_batches):
        logger.info(f"[CLASSIFICATION_SERVICE] Discovery Batch {i+1} of {len(sampled_batches)}...")
        
        batch_text = "\n\n---\n\n".join([c["text"] for c in batch if c.get("text")])
        
        prompt = f"""
You are a legal document architect. We are building a master list of 5 to 8 overarching clause categories for this document.
Categories discovered so far: {json.dumps(current_categories)}

Read this new batch of text from the document. 
If you find new major themes that aren't covered by the current categories, add them. 
Refine the list to be the 5 to 8 most essential, broad categories that can cover every clause in this document.
Do NOT create overly specific categories (e.g., use "Financial" instead of "Late Payment Fee").
Return a strict JSON array of the updated categories.
Example output: {{"categories": ["Termination", "Intellectual Property", "Financial", "General"]}}
"""
        try:
            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-20b", # Fast model for discovery
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Document Text Batch:\n{batch_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            res_json = json.loads(response.choices[0].message.content)
            current_categories = res_json.get("categories", current_categories)
            
            if i < len(sampled_batches) - 1:
                time.sleep(6)  # Rate limit safety
                
        except Exception as e:
            logger.error(f"[CLASSIFICATION_SERVICE] Error in discovery batch {i}: {e}")
            
    # Ensure "General" is always an option as a fallback
    if "General" not in current_categories:
        current_categories.append("General")
    
    # 100% Consistent Normalization (Strips whitespace and converts to Title Case)
    clean_categories = list(set([str(c).strip().title() for c in current_categories]))
    
    # Save to global classifications table securely (ignore existing)
    existing_res = supabase.table("classifications").select("name").in_("name", clean_categories).execute()
    existing_names = {row["name"] for row in existing_res.data}
    
    new_cats = [{"name": c} for c in clean_categories if c not in existing_names]
    if new_cats:
        logger.info(f"[CLASSIFICATION_SERVICE] Upserting {len(new_cats)} new categories to global pool...")
        supabase.table("classifications").insert(new_cats).execute()
        
    logger.info(f"[CLASSIFICATION_SERVICE] Final Discovered categories: {clean_categories}")
    return clean_categories


def analyze_batch(batch_chunks: list, dynamic_categories: list) -> list:
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
            {"role": "system", "content": get_system_prompt(dynamic_categories)},
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
        
    # 2. Category Discovery Workflow
    dynamic_categories = discover_categories(chunks, supabase)
    
    # 3. Batch chunks using our batching engine
    # Groq free tier for 120b model has a strict 8,000 TPM limit!
    # We use 2000 to be extremely safe and leave room for output tokens.
    batches = create_batches(chunks, max_tokens_per_batch=2000)
    
    # 4. Process ALL batches
    all_results = []
    
    for i, batch in enumerate(batches):
        logger.info(f"[CLASSIFICATION_SERVICE] Sending Batch {i+1} of {len(batches)} to Groq (openai/gpt-oss-120b). Processing {len(batch)} chunks...")
        
        results = analyze_batch(batch, dynamic_categories)
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