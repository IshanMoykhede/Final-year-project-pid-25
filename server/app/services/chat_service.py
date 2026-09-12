import os
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.core.supabase import connectSupa
from app.schemas.chat import RetrievedClause
from app.core.prompts import build_chat_system_prompt
from app.core.llm import generate_chat_completion

logger = logging.getLogger(__name__)

# Initialize models
try:
    logger.info("[CHAT_SERVICE] Loading all-MiniLM-L6-v2 HuggingFace model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"[CHAT_SERVICE] Failed to load embedding model: {e}")
    embedding_model = None


def answer_question(document_id: str, question: str, use_1hop_expansion: bool = True, generate_answer: bool = True) -> Dict[str, Any]:
    logger.info(f"Answering question for document_id: {document_id}. 1-Hop Expansion: {use_1hop_expansion}")
    supabase = connectSupa()

    if embedding_model is None:
        raise RuntimeError("Embedding model is not loaded.")

    # 1. Embed Query
    query_vector = embedding_model.encode(question).tolist()

    # 2. Vector Search (C_k)
    rpc_res = supabase.rpc("match_chunks", {
        "query_embedding": query_vector,
        "match_threshold": 0.2, # Lowered threshold to ensure we get some results
        "match_count": 5,
        "filter_document_id": document_id
    }).execute()
    
    top_k_chunks = rpc_res.data
    
    if not top_k_chunks:
        return {
            "success": True,
            "answer": "I could not find any relevant information in this document to answer your question.",
            "primary_clauses": [],
            "expanded_clauses": []
        }

    primary_clauses = []
    for c in top_k_chunks:
        primary_clauses.append(RetrievedClause(
            chunk_id=c["id"],
            chunk_no=c["chunk_no"],
            text=c["text"],
            aliases=c.get("aliases") or [],
            similarity=c.get("similarity"),
            is_expanded=False
        ))

    expanded_clauses = []
    
    # 3. 1-Hop Expansion (N_1)
    if use_1hop_expansion:
        source_chunk_ids = [c["id"] for c in top_k_chunks]
        
        refs = supabase.table("cross_references") \
            .select("target_chunk_id, reference_text") \
            .in_("source_chunk_id", source_chunk_ids) \
            .eq("link_type", "EXACT_MATCH") \
            .execute()
            
        target_ids = list(set(r["target_chunk_id"] for r in refs.data if r["target_chunk_id"]))
        
        if target_ids:
            expanded_res = supabase.table("chunks").select("id, chunk_no, text, aliases").in_("id", target_ids).execute()
            
            # Avoid adding clauses that are already in the primary set
            existing_ids = {c["id"] for c in top_k_chunks}
            for c in expanded_res.data:
                if c["id"] not in existing_ids:
                    expanded_clauses.append(RetrievedClause(
                        chunk_id=c["id"],
                        chunk_no=c["chunk_no"],
                        text=c["text"],
                        aliases=c.get("aliases") or [],
                        similarity=None,
                        is_expanded=True
                    ))
                    
    # 4. LLM Generation
    all_evidence = primary_clauses + expanded_clauses
    
    context_str = "=== PRIMARY RELEVANT CLAUSES ===\n"
    for chunk in primary_clauses:
        alias_label = ", ".join(chunk.aliases) if chunk.aliases else f"Clause {chunk.chunk_no}"
        context_str += f"\n--- [{alias_label}] ---\n{chunk.text}\n"

    if expanded_clauses:
        context_str += "\n=== CROSS-REFERENCED SUPPORTING CLAUSES ===\n"
        for chunk in expanded_clauses:
            alias_label = ", ".join(chunk.aliases) if chunk.aliases else f"Clause {chunk.chunk_no}"
            context_str += f"\n--- [{alias_label}] ---\n{chunk.text}\n"

    system_prompt = build_chat_system_prompt(context_str)

    answer = ""
    if generate_answer:
        answer = generate_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1
        )

    return {
        "success": True,
        "answer": answer,
        "primary_clauses": [c.model_dump() for c in primary_clauses],
        "expanded_clauses": [c.model_dump() for c in expanded_clauses]
    }
