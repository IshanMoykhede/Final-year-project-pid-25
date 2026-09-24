"""
One-time script to auto-generate evaluation questions from your actual Supabase
chunks and cross-references, then write them to dataset.json.

Run once:
    python -m app.evaluation.generate_dataset

After this, dataset.json is static and runner.py uses it every time.
"""

import os
import json
import time
import logging
from dotenv import load_dotenv
from groq import Groq
from app.core.supabase import connectSupa

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

# Documents to use for generation — only fully processed ones
TARGET_DOCUMENT_IDS = [
    "1af9efc4-e5e6-4ca3-a2dc-d1bfaaf5c744",  # Commercial Office Lease (28 chunks, 6 links)
    "d28c03f5-4d60-4bc9-b173-65af2ab9e8e7",  # Employee Leave Policy (43 chunks, 1 link)
    "efcaa98f-2437-46bc-863a-90809d6d8a44",  # CUAD Contract 2 (4 chunks, 2 links)
    "e6eb83ac-b3e5-4e22-b19a-089229bbcbb4",  # CUAD Contract 3 (11 chunks, 6 links)
    "6f4b2b06-c90b-4a81-a0c5-d273d24a34bf",  # Rental Agreement (7 chunks, 0 links)
]

# How many Direct questions to generate per chunk
DIRECT_QUESTIONS_PER_CHUNK = 1

# Max chunks to sample per document for Direct questions
MAX_CHUNKS_PER_DOC = 8


def generate_direct_question(chunk_text: str, chunk_aliases: list) -> dict | None:
    """Ask Groq to generate one Direct question + reference answer for a chunk."""
    alias_hint = ", ".join(chunk_aliases) if chunk_aliases else "this clause"
    prompt = f"""You are building an evaluation dataset for a legal RAG system.

Given this legal clause text:
---
{chunk_text[:1500]}
---

Known as: {alias_hint}

Generate ONE clear, specific question that can be answered directly from this clause.
Also provide the reference answer (1-2 sentences, factual, based only on the text).

Respond ONLY with this exact JSON:
{{"question": "...", "reference_answer": "..."}}
"""
    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=300
        )
        data = json.loads(response.choices[0].message.content)
        if data.get("question") and data.get("reference_answer"):
            return data
    except Exception as e:
        logger.warning(f"Failed to generate direct question: {e}")
    return None


def generate_hop_question(src_text: str, src_aliases: list, tgt_text: str, tgt_aliases: list, ref_text: str) -> dict | None:
    """Ask Groq to generate a 1-Hop Dependent question that bridges two chunks."""
    src_alias = ", ".join(src_aliases) if src_aliases else "the source clause"
    tgt_alias = ", ".join(tgt_aliases) if tgt_aliases else "the referenced clause"
    prompt = f"""You are building an evaluation dataset for a legal RAG system that tests cross-reference retrieval.

Source clause ({src_alias}):
---
{src_text[:800]}
---

This clause references "{ref_text}", which points to:

Target clause ({tgt_alias}):
---
{tgt_text[:800]}
---

Generate ONE question that requires understanding BOTH clauses to answer fully.
The question should naturally lead a reader from the source clause to the referenced target clause.
Also provide the reference answer (2-3 sentences) that synthesises both clauses.

Respond ONLY with this exact JSON:
{{"question": "...", "reference_answer": "..."}}
"""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=400
            )
            data = json.loads(response.choices[0].message.content)
            if data.get("question") and data.get("reference_answer"):
                return data
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "rate limit" in err:
                wait = 15 * attempt
                logger.warning(f"  Rate limit hit on 1-Hop generation (attempt {attempt}/{max_retries}). Waiting {wait}s...")
                time.sleep(wait)
            else:
                logger.warning(f"  Failed to generate 1-hop question (attempt {attempt}): {e}")
                time.sleep(5)
    return None


def main():
    supabase = connectSupa()
    
    # Load existing dataset to append to (don't overwrite what we have)
    output_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        logger.info(f"Loaded {len(dataset)} existing questions from dataset.json. Will append new ones.")
        # Track already-covered (doc_id, question) pairs to avoid duplicates
        existing_questions = {(q["document_id"], q["question"]) for q in dataset}
    else:
        dataset = []
        existing_questions = set()

    total_direct = 0
    total_hop = 0

    for doc_id in TARGET_DOCUMENT_IDS:
        logger.info(f"\n=== Processing document: {doc_id} ===")

        # Fetch chunks — must include chunk_no and text for both Direct and 1-Hop generation
        chunks_res = supabase.table("chunks") \
            .select("id, chunk_no, text, aliases") \
            .eq("document_id", doc_id) \
            .order("chunk_no") \
            .execute()
        chunks = [c for c in chunks_res.data if c.get("chunk_no") is not None and c.get("text")]

        if not chunks:
            logger.warning(f"No chunks found for {doc_id}, skipping.")
            continue

        logger.info(f"Found {len(chunks)} chunks.")
        id_to_chunk = {c["id"]: c for c in chunks}

        # Fetch resolved cross-references
        refs_res = supabase.table("cross_references") \
            .select("source_chunk_id, target_chunk_id, reference_text, link_type") \
            .eq("document_id", doc_id) \
            .eq("link_type", "EXACT_MATCH") \
            .execute()
        resolved_refs = [r for r in refs_res.data if r.get("target_chunk_id") and r["target_chunk_id"] in id_to_chunk]
        logger.info(f"Found {len(resolved_refs)} resolved cross-references.")

        # --- Generate Direct questions ---
        # Sample evenly across the document
        sampled_chunks = chunks[:MAX_CHUNKS_PER_DOC]
        if len(chunks) > MAX_CHUNKS_PER_DOC:
            step = len(chunks) // MAX_CHUNKS_PER_DOC
            sampled_chunks = [chunks[i] for i in range(0, len(chunks), step)][:MAX_CHUNKS_PER_DOC]

        for i, chunk in enumerate(sampled_chunks):
            if len(chunk.get("text", "")) < 100:
                continue  # skip very short chunks

            logger.info(f"  Generating Direct question for chunk {chunk['chunk_no']} ({chunk.get('aliases', [])})...")
            result = generate_direct_question(chunk["text"], chunk.get("aliases") or [])

            if result:
                key = (doc_id, result["question"])
                if key not in existing_questions:
                    dataset.append({
                        "document_id": doc_id,
                        "query_type": "Direct",
                        "question": result["question"],
                        "gold_chunk_nos": [chunk["chunk_no"]],
                        "gold_referenced_chunk_no": None,
                        "reference_answer": result["reference_answer"]
                    })
                    existing_questions.add(key)
                    total_direct += 1
                    logger.info(f"    Q: {result['question'][:70]}...")

            # Rate limit safety
            time.sleep(2)

        # --- Generate 1-Hop Dependent questions ---
        for ref in resolved_refs:
            src_chunk = id_to_chunk.get(ref["source_chunk_id"])
            tgt_chunk = id_to_chunk.get(ref["target_chunk_id"])

            if not src_chunk or not tgt_chunk:
                logger.warning(f"  Skipping ref — missing src or tgt chunk.")
                continue

            if not src_chunk.get("text") or not tgt_chunk.get("text"):
                logger.warning(f"  Skipping ref — missing text in chunk {src_chunk.get('chunk_no')} or {tgt_chunk.get('chunk_no')}.")
                continue

            logger.info(f"  Generating 1-Hop question: Chunk {src_chunk['chunk_no']} -> Chunk {tgt_chunk['chunk_no']} via '{ref['reference_text']}'...")
            result = generate_hop_question(
                src_text=src_chunk["text"],
                src_aliases=src_chunk.get("aliases") or [],
                tgt_text=tgt_chunk["text"],
                tgt_aliases=tgt_chunk.get("aliases") or [],
                ref_text=ref["reference_text"]
            )

            if result:
                key = (doc_id, result["question"])
                if key not in existing_questions:
                    dataset.append({
                        "document_id": doc_id,
                        "query_type": "1-Hop Dependent",
                        "question": result["question"],
                        "gold_chunk_nos": [src_chunk["chunk_no"]],
                        "gold_referenced_chunk_no": tgt_chunk["chunk_no"],
                        "reference_answer": result["reference_answer"]
                    })
                    existing_questions.add(key)
                    total_hop += 1
                    logger.info(f"    Q: {result['question'][:70]}...")

            time.sleep(8)

        logger.info(f"  1-Hop questions generated: {total_hop}")

    # Save to dataset.json
    output_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    logger.info(f"\n=== Generation Complete ===")
    logger.info(f"Total Direct questions:      {total_direct}")
    logger.info(f"Total 1-Hop questions:       {total_hop}")
    logger.info(f"Total questions in dataset:  {len(dataset)}")
    logger.info(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
