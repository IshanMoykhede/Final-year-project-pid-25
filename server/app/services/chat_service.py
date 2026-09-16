import os
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, CrossEncoder
from app.core.supabase import connectSupa
from app.schemas.chat import RetrievedClause
from app.core.prompts import build_chat_system_prompt
from app.core.llm import generate_chat_completion

logger = logging.getLogger(__name__)

# Initialize models lazily
embedding_model = None
reranker_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        try:
            logger.info("[CHAT_SERVICE] Loading all-MiniLM-L6-v2 HuggingFace embedding model...")
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"[CHAT_SERVICE] Failed to load embedding model: {e}")
            raise RuntimeError("Embedding model failed to load.")
    return embedding_model

def get_reranker_model():
    global reranker_model
    if reranker_model is None:
        try:
            logger.info("[CHAT_SERVICE] Loading cross-encoder/ms-marco-MiniLM-L-6-v2 reranker model...")
            reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except Exception as e:
            logger.warning(f"[CHAT_SERVICE] Failed to load cross-encoder model: {e}. Fallback to standard bi-encoder scores.")
            # Set to a dummy object or handle gracefully
            reranker_model = False # Use False to distinguish from None (not loaded yet)
    return reranker_model if reranker_model is not False else None


def answer_question(document_id: str, question: str, use_1hop_expansion: bool = True, generate_answer: bool = True) -> Dict[str, Any]:
    logger.info(f"Answering question for document_id: {document_id}. 1-Hop Expansion: {use_1hop_expansion}")
    supabase = connectSupa()

    emb_model = get_embedding_model()
    rerank_model = get_reranker_model()

    # 1. Embed Query
    query_vector = emb_model.encode(question).tolist()

    # Detect summary / global overview intent
    summary_keywords = [
        "summarize", "summary", "overview", "all policies", "key provisions",
        "what is this document about", "all rules", "main points", "all leaves",
        "leave policy", "leave policies", "entire policy", "full policy"
    ]
    is_summary_query = any(kw in question.lower() for kw in summary_keywords)

    if is_summary_query:
        # Fetch broader candidate pool for summary
        candidate_count = 25
        final_top_k = 15
        match_threshold = 0.10
        logger.info(f"[CHAT_SERVICE] Summary intent detected. Candidate count={candidate_count}, final_top_k={final_top_k}")
    else:
        # Standard Q&A: Fetch top 20 candidates for Stage 2 Cross-Encoder reranking
        candidate_count = 20
        final_top_k = 5
        match_threshold = 0.15

    # 2. Stage 1: Vector Search Candidates (Bi-Encoder Retrieval)
    rpc_res = supabase.rpc("match_chunks", {
        "query_embedding": query_vector,
        "match_threshold": match_threshold,
        "match_count": candidate_count,
        "filter_document_id": document_id
    }).execute()
    
    candidates = rpc_res.data
    
    if not candidates:
        return {
            "success": True,
            "answer": "I could not find any relevant information in this document to answer your question.",
            "primary_clauses": [],
            "expanded_clauses": []
        }

    # 3. Stage 2: Cross-Encoder Reranking (High precision semantic ranking)
    if rerank_model is not None and len(candidates) > 1:
        try:
            pairs = [[question, c["text"]] for c in candidates]
            scores = rerank_model.predict(pairs)
            for i, c in enumerate(candidates):
                c["rerank_score"] = float(scores[i])
            candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
            logger.info(f"[CHAT_SERVICE] CrossEncoder successfully reranked {len(candidates)} candidates. Top score: {candidates[0]['rerank_score']:.4f}")
        except Exception as re:
            logger.error(f"[CHAT_SERVICE] CrossEncoder reranking failed, falling back to vector similarity: {re}")

    top_k_chunks = candidates[:final_top_k]

    primary_clauses = []
    for c in top_k_chunks:
        primary_clauses.append(RetrievedClause(
            chunk_id=c["id"],
            chunk_no=c["chunk_no"],
            text=c["text"],
            aliases=c.get("aliases") or [],
            similarity=c.get("rerank_score") if "rerank_score" in c else c.get("similarity"),
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
