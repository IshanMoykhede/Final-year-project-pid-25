import logging
from app.core.supabase import connectSupa

logger = logging.getLogger(__name__)

def resolve_cross_references(file_id: str):
    """
    Connects the bridge! Finds all 'AI_SUGGESTED' references and tries to match them
    to the aliases of the chunks in the document.
    """
    logger.info(f"Starting cross-reference resolution for document_id: {file_id}")
    supabase = connectSupa()
    
    # 1. Fetch all chunks and their aliases for this document
    chunks_result = supabase.table("chunks").select("id, aliases").eq("document_id", file_id).execute()
    chunks = chunks_result.data
    
    if not chunks:
        logger.warning(f"No chunks found to link for document_id: {file_id}")
        return
        
    # 2. Fetch all unresolved AI_SUGGESTED references for this document
    refs_result = supabase.table("cross_references") \
        .select("id, reference_text") \
        .eq("document_id", file_id) \
        .eq("link_type", "AI_SUGGESTED") \
        .execute()
        
    references = refs_result.data
    
    if not references:
        logger.info("No AI_SUGGESTED references found to resolve.")
        return
        
    logger.info(f"Found {len(references)} AI_SUGGESTED references to resolve.")
    
    resolved_count = 0
    unresolved_count = 0
    
    # 3. Match each reference to a chunk's alias
    for ref in references:
        ref_id = ref["id"]
        ref_text = ref["reference_text"].strip().lower()
        
        target_chunk_id = None
        
        # Search through all chunks to see if any alias matches
        for chunk in chunks:
            # Safely handle if aliases is None
            chunk_aliases = chunk.get("aliases") or []
            
            # Check if any alias in this chunk matches our reference text (case insensitive)
            if any(alias.strip().lower() == ref_text for alias in chunk_aliases):
                target_chunk_id = chunk["id"]
                break # We found a match, stop looking!
                
        # 4. Update the database
        if target_chunk_id:
            # We found a hard link!
            supabase.table("cross_references").update({
                "target_chunk_id": target_chunk_id,
                "link_type": "EXACT_MATCH"
            }).eq("id", ref_id).execute()
            resolved_count += 1
        else:
            # No chunk goes by this nickname. Mark it unresolved so we don't try again.
            supabase.table("cross_references").update({
                "link_type": "UNRESOLVED"
            }).eq("id", ref_id).execute()
            unresolved_count += 1
            
    logger.info(f"Resolution complete: {resolved_count} EXACT_MATCH, {unresolved_count} UNRESOLVED.")
    
    return {
        "resolved": resolved_count,
        "unresolved": unresolved_count
    }
