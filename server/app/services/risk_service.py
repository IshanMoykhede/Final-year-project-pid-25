import logging
import json
import os
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from groq import AsyncGroq
from app.core.supabase import connectSupa
from app.schemas.AnalyzerSchemas import (
    DocumentRiskResponse,
    BatchRiskResponse,
    RiskItem,
    RawBatchRiskResponse,
    RawRiskItem
)
from app.services.chunkBatching import create_batches
from pydantic import ValidationError

load_dotenv()
logger = logging.getLogger(__name__)

def get_risk_model_name() -> str:
    """Returns the configured model for risk analysis, defaulting to fast & cheap openai/gpt-oss-20b."""
    return os.getenv("GROQ_RISK_MODEL", "openai/gpt-oss-20b")

async def call_groq_with_retry(groq_client: AsyncGroq, model: str, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
    """Executes chat completion on Groq asynchronously with exponential backoff on rate limits."""
    backoff = 3.0
    for attempt in range(1, max_retries + 1):
        try:
            completion = await groq_client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048
            )
            return completion.choices[0].message.content or "{}"
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "rate limit" in err_msg or "too many requests" in err_msg:
                logger.warning(f"[RISK_SERVICE] Groq rate limit hit. Backing off {backoff:.1f}s (attempt {attempt}/{max_retries})...")
                await asyncio.sleep(backoff)
                backoff *= 2.0
            elif attempt == max_retries:
                logger.error(f"[RISK_SERVICE] Failed calling Groq after {max_retries} attempts: {e}")
                raise
            else:
                logger.warning(f"[RISK_SERVICE] Transient error: {e}. Retrying in 2.0s...")
                await asyncio.sleep(2.0)
    return "{}"

async def analyze_document_risks(file_id: str, force_refresh: bool = False) -> DocumentRiskResponse:
    """
    Analyzes all clauses in a document for legal risks using a fast & cost-effective LLM concurrently.
    Caches the result in the `files` table under `risk_cache` to ensure instant sub-100ms retrieval.
    """
    supabase = connectSupa()
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured in environment.")

    groq_client = AsyncGroq(api_key=groq_api_key)
    model_name = get_risk_model_name()

    # 1. Check DB Cache First (Instant Return)
    if not force_refresh:
        try:
            file_record = supabase.table("files").select("risk_cache").eq("id", file_id).execute()
            if not file_record.data:
                raise ValueError(f"File {file_id} not found.")

            cached = file_record.data[0].get("risk_cache")
            if cached and isinstance(cached, dict) and "high_risks" in cached:
                logger.info(f"[RISK_SERVICE] Cache hit! Returning instant risk analysis for {file_id}")
                return DocumentRiskResponse(**cached)
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"[RISK_SERVICE] Cache check failed (possibly column missing): {e}")

    logger.info(f"[RISK_SERVICE] Generating risk analysis for document {file_id} using model {model_name}...")

    # 2. Fetch all chunks for this document
    chunks_res = supabase.table("chunks").select("id, text").eq("document_id", file_id).execute()
    chunks = chunks_res.data

    if not chunks:
        raise ValueError("No text chunks found for this document. Has the document completed preprocessing?")

    # Map chunk id to text for verification and context
    chunk_map = {c["id"]: c.get("text", "") for c in chunks}

    # Filter out empty or trivial chunks (e.g. page headers / short numbers)
    valid_chunks = [c for c in chunks if c.get("text") and len(c["text"].strip()) > 30]

    # 3. Create batches to respect context windows (max ~4000 tokens per batch to reduce round-trips)
    batches = create_batches(valid_chunks, max_tokens_per_batch=4000)
    logger.info(f"[RISK_SERVICE] Grouped {len(valid_chunks)} chunks into {len(batches)} batches for concurrent LLM evaluation.")

    system_prompt = (
        "You are an expert legal risk and compliance auditor. Review contract clauses and identify genuine legal or financial risks.\n\n"
        "SEVERITY CRITERIA (Strictly adhere to these definitions):\n"
        "- HIGH: Substantial uncapped liability, major financial exposure, termination/control risk, or materially one-sided obligation.\n"
        "- MEDIUM: Meaningful but limited contractual exposure or moderately unfavorable obligation.\n"
        "- LOW: Minor exposure, ambiguity, or limited operational concern.\n\n"
        "RULES:\n"
        "1. DO NOT match keywords blindly. Evaluate the real-world substance and balance of the clause.\n"
        "2. If standard/balanced boilerplate, DO NOT flag it.\n"
        "3. For genuine risks only, output JSON with 'risks' array containing:\n"
        "   - 'chunk_id': exact chunk UUID from input\n"
        "   - 'clause_title': concise title (e.g. 'Uncapped Indemnity', 'Post-Termination Restraint')\n"
        "   - 'risk_level': exactly 'HIGH', 'MEDIUM', or 'LOW'\n"
        "   - 'explanation': 1-2 sentence plain-language explanation of the worst-case exposure\n"
        "   - 'compliance_check': statutory validity, legal enforceability (cite relevant Acts/Sections where applicable), or market standard\n"
        "   - 'recommendation': clear, actionable advice on how the reviewing party should modify, cap, or negotiate the clause\n\n"
        "Format: {\"risks\": [{\"chunk_id\": \"...\", \"clause_title\": \"...\", \"risk_level\": \"HIGH\"|\"MEDIUM\"|\"LOW\", \"explanation\": \"...\", \"compliance_check\": \"...\", \"recommendation\": \"...\"}]}"
    )

    # Concurrency control: limit simultaneous API calls to 4 to avoid Groq TPM/RPM spikes
    semaphore = asyncio.Semaphore(4)

    async def process_batch(idx: int, batch: List[Dict[str, Any]]) -> List[RiskItem]:
        batch_risks: List[RiskItem] = []
        batch_content = [f"[[CHUNK_ID: {c['id']}]]\n{c['text']}" for c in batch]
        batch_text = "\n\n".join(batch_content)
        user_prompt = f"Evaluate risks in these {len(batch)} clauses:\n\n{batch_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        async with semaphore:
            try:
                logger.info(f"[RISK_SERVICE] Launching batch {idx}/{len(batches)} ({len(batch)} clauses)...")
                raw_response = await call_groq_with_retry(groq_client, model_name, messages)
                
                # Deep Schema Validation using Pydantic
                try:
                    parsed_payload = json.loads(raw_response)
                except json.JSONDecodeError as json_err:
                    logger.error(f"[RISK_SERVICE] Batch {idx}: Malformed JSON returned by LLM: {json_err}")
                    return []

                raw_risks_list = parsed_payload.get("risks", [])
                if not isinstance(raw_risks_list, list):
                    logger.warning(f"[RISK_SERVICE] Batch {idx}: 'risks' key is not a list.")
                    return []

                for raw_item in raw_risks_list:
                    if not isinstance(raw_item, dict):
                        continue
                    # Normalize risk_level if casing is mismatched
                    raw_level = str(raw_item.get("risk_level", "")).strip().upper()
                    if raw_level == "MID":
                        raw_level = "MEDIUM"
                    raw_item["risk_level"] = raw_level

                    try:
                        validated_risk = RawRiskItem.model_validate(raw_item)
                    except ValidationError as ve:
                        logger.warning(f"[RISK_SERVICE] Batch {idx}: Skipping invalid risk schema: {ve.errors()} | Data: {raw_item}")
                        continue

                    # Verify valid chunk_id matching input document chunks
                    if validated_risk.chunk_id not in chunk_map:
                        logger.warning(f"[RISK_SERVICE] Batch {idx}: Unknown chunk_id '{validated_risk.chunk_id}' returned by LLM. Skipping.")
                        continue

                    batch_risks.append(
                        RiskItem(
                            chunk_id=validated_risk.chunk_id,
                            chunk_text=chunk_map[validated_risk.chunk_id],
                            risk_level=validated_risk.risk_level,
                            clause_title=validated_risk.clause_title.strip(),
                            explanation=validated_risk.explanation.strip(),
                            compliance_check=validated_risk.compliance_check.strip(),
                            recommendation=validated_risk.recommendation.strip()
                        )
                    )

            except Exception as e:
                logger.error(f"[RISK_SERVICE] Error processing batch {idx}: {e}")
                return []

        return batch_risks

    # Run batches concurrently with asyncio.gather
    tasks = [process_batch(idx, batch) for idx, batch in enumerate(batches, start=1)]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    detected_risks: List[RiskItem] = []
    for batch_res in results:
        detected_risks.extend(batch_res)

    # 4. Partition into High, Medium, and Low severity
    high_list: List[RiskItem] = [r for r in detected_risks if r.risk_level == "HIGH"]
    medium_list: List[RiskItem] = [r for r in detected_risks if r.risk_level == "MEDIUM"]
    low_list: List[RiskItem] = [r for r in detected_risks if r.risk_level == "LOW"]

    total_count = len(high_list) + len(medium_list) + len(low_list)

    final_response = DocumentRiskResponse(
        high_risks=high_list,
        medium_risks=medium_list,
        low_risks=low_list,
        total_risks=total_count
    )

    # 5. Cache result in Supabase files table (for instant future lookups)
    try:
        logger.info(f"[RISK_SERVICE] Caching risk analysis result for file {file_id} ({total_count} total risks)...")
        supabase.table("files").update({"risk_cache": final_response.model_dump()}).eq("id", file_id).execute()
        logger.info(f"[RISK_SERVICE] Successfully cached risk analysis in files table.")
    except Exception as e:
        logger.warning(
            f"[RISK_SERVICE] Could not persist to 'files.risk_cache'. "
            f"If the column does not exist, run 'ALTER TABLE files ADD COLUMN IF NOT EXISTS risk_cache JSONB;'. Detail: {e}"
        )

    return final_response
