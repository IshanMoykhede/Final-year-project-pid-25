import logging
import json
import os
import asyncio
import re
from typing import List, Dict, Any

from dotenv import load_dotenv
from groq import AsyncGroq
from app.core.supabase import connectSupa
from app.schemas.AnalyzerSchemas import (
    DocumentRiskResponse,
    RiskItem,
    RawRiskItem,
)
from app.services.chunkBatching import create_batches
from pydantic import ValidationError


load_dotenv()
logger = logging.getLogger(__name__)


def get_risk_model_name() -> str:
    """
    Returns the configured model for legal risk analysis.
    """
    return os.getenv(
        "GROQ_RISK_MODEL",
        "openai/gpt-oss-120b"
    )


async def call_groq_with_retry(
    groq_client: AsyncGroq,
    model: str,
    messages: List[Dict[str, str]],
    max_retries: int = 5
) -> str:
    """
    Execute a Groq chat completion with retry/backoff handling.
    """

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

            # Rate-limit handling
            if (
                "429" in err_msg
                or "rate limit" in err_msg
                or "too many requests" in err_msg
            ):
                match = re.search(
                    r"try again in ([\d\.]+)s",
                    err_msg
                )

                if match:
                    wait_time = float(match.group(1)) + 1.5
                else:
                    wait_time = min(
                        60.0,
                        backoff
                    )

                logger.warning(
                    f"[RISK_SERVICE] Groq rate limit hit. "
                    f"Waiting {wait_time:.1f}s "
                    f"(attempt {attempt}/{max_retries})..."
                )

                if attempt < max_retries:
                    await asyncio.sleep(wait_time)

                backoff *= 2.0

            # Final failure
            elif attempt == max_retries:
                logger.error(
                    f"[RISK_SERVICE] Failed calling Groq "
                    f"after {max_retries} attempts: {e}"
                )
                raise

            # Other transient errors
            else:
                logger.warning(
                    f"[RISK_SERVICE] Transient error: {e}. "
                    f"Retrying in 2.0s..."
                )

                await asyncio.sleep(2.0)

    return "{}"


async def analyze_document_risks(
    file_id: str,
    force_refresh: bool = False
) -> DocumentRiskResponse:
    """
    Analyze all meaningful clauses in a document for legal,
    operational, and financial risks.

    Results are cached in files.risk_cache.
    """

    supabase = connectSupa()

    groq_api_key = os.getenv("GROQ_API_KEY", "")

    if not groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured in environment."
        )

    groq_client = AsyncGroq(
        api_key=groq_api_key
    )

    model_name = get_risk_model_name()

    # ==========================================================
    # 1. CHECK CACHE
    # ==========================================================

    if not force_refresh:
        try:
            file_record = (
                supabase
                .table("files")
                .select("risk_cache")
                .eq("id", file_id)
                .execute()
            )

            if not file_record.data:
                raise ValueError(
                    f"File {file_id} not found."
                )

            cached = file_record.data[0].get(
                "risk_cache"
            )

            if (
                cached
                and isinstance(cached, dict)
                and "high_risks" in cached
            ):
                logger.info(
                    f"[RISK_SERVICE] Cache hit for {file_id}"
                )

                return DocumentRiskResponse(
                    **cached
                )

        except ValueError:
            raise

        except Exception as e:
            logger.warning(
                f"[RISK_SERVICE] Cache check failed: {e}"
            )

    logger.info(
        f"[RISK_SERVICE] Generating risk analysis "
        f"for {file_id} using {model_name}"
    )

    # ==========================================================
    # 2. FETCH DOCUMENT CHUNKS
    # ==========================================================

    chunks_res = (
        supabase
        .table("chunks")
        .select("id, text")
        .eq("document_id", file_id)
        .execute()
    )

    chunks = chunks_res.data or []

    if not chunks:
        raise ValueError(
            "No text chunks found for this document. "
            "Has document preprocessing completed?"
        )

    # Map real chunk IDs to text
    chunk_map = {
        c["id"]: c.get("text", "")
        for c in chunks
    }

    # Remove empty / trivial chunks
    valid_chunks = [
        c
        for c in chunks
        if c.get("text")
        and len(c["text"].strip()) > 30
    ]

    if not valid_chunks:
        logger.warning(
            f"[RISK_SERVICE] No meaningful chunks found "
            f"for document {file_id}"
        )

        return DocumentRiskResponse(
            high_risks=[],
            medium_risks=[],
            low_risks=[],
            total_risks=0
        )

    # ==========================================================
    # 3. CREATE BATCHES
    # ==========================================================

    batches = create_batches(
        valid_chunks,
        max_tokens_per_batch=3000
    )

    logger.info(
        f"[RISK_SERVICE] Grouped "
        f"{len(valid_chunks)} chunks into "
        f"{len(batches)} batches"
    )

    # ==========================================================
    # 4. SYSTEM PROMPT
    # ==========================================================

    system_prompt = (
        "You are a legal risk and compliance analysis assistant.\n\n"

        "Your task is to examine contract or policy clauses "
        "and identify genuine legal, financial, and operational risks.\n\n"

        "SEVERITY CRITERIA:\n"
        "- HIGH: Substantial legal or financial exposure, "
        "major termination/control risk, uncapped liability, "
        "or materially one-sided obligations.\n"

        "- MEDIUM: Meaningful but limited contractual exposure, "
        "moderately unfavorable obligations, or significant ambiguity.\n"

        "- LOW: Minor exposure, limited ambiguity, "
        "or relatively small operational concerns.\n\n"

        "RISK SCORE:\n"
        "- HIGH should generally correspond to 80-100.\n"
        "- MEDIUM should generally correspond to 40-79.\n"
        "- LOW should generally correspond to 1-39.\n\n"

        "RULES:\n"

        "1. Evaluate the actual substance of each clause. "
        "Do not classify risks using keywords alone.\n"

        "2. Do not flag ordinary, balanced, or standard "
        "boilerplate provisions merely because they contain "
        "legal terminology.\n"

        "3. Analyze only the supplied clause text. "
        "Do not invent facts or missing provisions.\n"

        "4. Because the input may contain only fragments of a "
        "larger document, do not claim that a protection, "
        "right, procedure, or limitation is absent unless "
        "the supplied clause explicitly establishes that absence.\n"

        "5. Every returned clause_index must correspond exactly "
        "to one of the [[CLAUSE INDEX: n]] identifiers in the input.\n"

        "6. Return only genuine risks. Do not create a risk "
        "for every clause.\n\n"

        "7. Keep 'explanation', 'compliance_check', and 'recommendation' "
        "concise (1-2 sentences each). Never reproduce long quotes.\n\n"

        "OUTPUT FORMAT:\n"
        "{"
        "\"risks\": ["
        "{"
        "\"clause_index\": 1,"
        "\"clause_title\": \"...\","
        "\"risk_level\": \"HIGH|MEDIUM|LOW\","
        "\"risk_score\": 85,"
        "\"explanation\": \"...\","
        "\"compliance_check\": \"...\","
        "\"recommendation\": \"...\""
        "}"
        "]"
        "}\n\n"

        "The risk_score must be an integer from 1 to 100."
    )

    # ==========================================================
    # 5. CONCURRENCY CONTROL
    # ==========================================================

    # Four concurrent requests.
    # Reduce to 1 or 2 if Groq TPM/RPM limits are reached.
    semaphore = asyncio.Semaphore(2)

    async def process_batch(
        idx: int,
        batch: List[Dict[str, Any]]
    ) -> List[RiskItem]:

        batch_risks: List[RiskItem] = []

        # Give the LLM deterministic local indices instead
        # of exposing database UUIDs.
        batch_content = [
            f"[[CLAUSE INDEX: {i + 1}]]\n{c['text']}"
            for i, c in enumerate(batch)
        ]

        batch_text = "\n\n".join(
            batch_content
        )

        user_prompt = (
            f"Evaluate the following {len(batch)} clauses "
            f"for genuine legal, financial, or operational risks and respond with a valid JSON object:\n\n"
            f"{batch_text}"
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        async with semaphore:

            try:
                logger.info(
                    f"[RISK_SERVICE] Processing batch "
                    f"{idx}/{len(batches)} "
                    f"({len(batch)} clauses)"
                )

                raw_response = await call_groq_with_retry(
                    groq_client,
                    model_name,
                    messages
                )

                # ==================================================
                # JSON PARSING
                # ==================================================

                try:
                    parsed_payload = json.loads(
                        raw_response
                    )

                except json.JSONDecodeError as e:
                    logger.error(
                        f"[RISK_SERVICE] Batch {idx}: "
                        f"Malformed JSON: {e}"
                    )
                    return []

                raw_risks_list = parsed_payload.get(
                    "risks",
                    []
                )

                if not isinstance(
                    raw_risks_list,
                    list
                ):
                    logger.warning(
                        f"[RISK_SERVICE] Batch {idx}: "
                        "'risks' is not a list."
                    )
                    return []

                # ==================================================
                # VALIDATE EACH RISK
                # ==================================================

                for raw_item in raw_risks_list:

                    if not isinstance(
                        raw_item,
                        dict
                    ):
                        continue

                    # Normalize severity
                    raw_level = str(
                        raw_item.get(
                            "risk_level",
                            ""
                        )
                    ).strip().upper()

                    if raw_level == "MID":
                        raw_level = "MEDIUM"

                    raw_item["risk_level"] = raw_level

                    # Validate / normalize risk score
                    raw_score = raw_item.get(
                        "risk_score"
                    )

                    if raw_score is None:
                        # Only a neutral fallback for malformed
                        # model output. This is NOT a classification
                        # override.
                        if raw_level == "HIGH":
                            raw_score = 80
                        elif raw_level == "MEDIUM":
                            raw_score = 60
                        elif raw_level == "LOW":
                            raw_score = 20
                        else:
                            raw_score = 1

                    try:
                        raw_score = int(
                            raw_score
                        )
                    except (TypeError, ValueError):
                        logger.warning(
                            f"[RISK_SERVICE] Batch {idx}: "
                            f"Invalid risk_score: {raw_score}"
                        )
                        continue

                    # Keep score inside valid range
                    raw_score = max(
                        1,
                        min(100, raw_score)
                    )

                    raw_item["risk_score"] = raw_score

                    # ==================================================
                    # PYDANTIC VALIDATION
                    # ==================================================

                    try:
                        validated_risk = (
                            RawRiskItem.model_validate(
                                raw_item
                            )
                        )

                    except ValidationError as ve:
                        logger.warning(
                            f"[RISK_SERVICE] Batch {idx}: "
                            f"Invalid risk schema: "
                            f"{ve.errors()}"
                        )
                        continue

                    # ==================================================
                    # VERIFY CLAUSE INDEX
                    # ==================================================

                    c_idx = (
                        validated_risk.clause_index - 1
                    )

                    if (
                        c_idx < 0
                        or c_idx >= len(batch)
                    ):
                        logger.warning(
                            f"[RISK_SERVICE] Batch {idx}: "
                            f"Invalid clause_index "
                            f"{validated_risk.clause_index}"
                        )
                        continue

                    # Map temporary integer index back
                    # to the real database UUID.
                    matched_chunk = batch[c_idx]

                    real_chunk_id = matched_chunk["id"]

                    # ==================================================
                    # BUILD FINAL RISK OBJECT
                    # ==================================================

                    batch_risks.append(
                        RiskItem(
                            chunk_id=real_chunk_id,
                            chunk_text=chunk_map[
                                real_chunk_id
                            ],
                            risk_level=(
                                validated_risk.risk_level
                            ),
                            risk_score=(
                                validated_risk.risk_score
                            ),
                            clause_title=(
                                validated_risk
                                .clause_title
                                .strip()
                            ),
                            explanation=(
                                validated_risk
                                .explanation
                                .strip()
                            ),
                            compliance_check=(
                                validated_risk
                                .compliance_check
                                .strip()
                            ),
                            recommendation=(
                                validated_risk
                                .recommendation
                                .strip()
                            )
                        )
                    )

            except Exception as e:
                logger.error(
                    f"[RISK_SERVICE] Error processing "
                    f"batch {idx}: {e}"
                )

                return []

        return batch_risks

    # ==========================================================
    # 6. PROCESS ALL BATCHES
    # ==========================================================

    tasks = [
        process_batch(
            idx,
            batch
        )
        for idx, batch in enumerate(
            batches,
            start=1
        )
    ]

    results = await asyncio.gather(
        *tasks,
        return_exceptions=False
    )

    # Flatten results
    detected_risks: List[RiskItem] = []

    for batch_result in results:
        detected_risks.extend(
            batch_result
        )

    # ==========================================================
    # 7. PARTITION BY SEVERITY
    # ==========================================================

    high_list = [
        r
        for r in detected_risks
        if r.risk_level == "HIGH"
    ]

    medium_list = [
        r
        for r in detected_risks
        if r.risk_level == "MEDIUM"
    ]

    low_list = [
        r
        for r in detected_risks
        if r.risk_level == "LOW"
    ]

    total_count = (
        len(high_list)
        + len(medium_list)
        + len(low_list)
    )

    # ==========================================================
    # 8. BUILD RESPONSE
    # ==========================================================

    final_response = DocumentRiskResponse(
        high_risks=high_list,
        medium_risks=medium_list,
        low_risks=low_list,
        total_risks=total_count
    )

    # ==========================================================
    # 9. CACHE RESULT
    # ==========================================================

    try:
        logger.info(
            f"[RISK_SERVICE] Caching "
            f"{total_count} risks for {file_id}"
        )

        (
            supabase
            .table("files")
            .update({
                "risk_cache": final_response.model_dump()
            })
            .eq("id", file_id)
            .execute()
        )

        logger.info(
            "[RISK_SERVICE] Risk analysis cached successfully."
        )

    except Exception as e:
        logger.warning(
            f"[RISK_SERVICE] Could not persist risk_cache: {e}"
        )

    return final_response

