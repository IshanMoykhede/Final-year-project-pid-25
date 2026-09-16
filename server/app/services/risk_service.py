import json
import logging
import os

from groq import Groq

from app.core.supabase import connectSupa
from app.schemas.risk import ClauseRisk, RiskAnalysisResponse

logger = logging.getLogger(__name__)


def analyze_document_risk(file_id: str, force_refresh: bool = False) -> dict:
    supabase = connectSupa()
    chunks_result = (
        supabase.table("chunks")
        .select("id, text, classification_id")
        .eq("document_id", file_id)
        .execute()
    )
    chunks = chunks_result.data or []
    if not chunks:
        raise ValueError("No chunks found. Is the document preprocessed?")

    classifications = supabase.table("classifications").select("id, name").execute().data or []
    category_by_id = {item["id"]: item["name"] for item in classifications}

    cached_result = supabase.table("clause_analysis").select("*").in_("chunk_id", [item["id"] for item in chunks]).execute()
    cached_by_chunk = {item["chunk_id"]: item for item in (cached_result.data or [])}
    if not force_refresh and len(cached_by_chunk) == len(chunks):
        return _build_response(chunks, cached_by_chunk, category_by_id)

    missing_chunks = [item for item in chunks if force_refresh or item["id"] not in cached_by_chunk]
    prompt_chunks = [
        {"chunk_id": item["id"], "category": category_by_id.get(item.get("classification_id"), "Unclassified"), "text": item["text"][:4000]}
        for item in missing_chunks
    ]
    client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful legal document risk reviewer. Assess each clause for practical risk to a non-lawyer. "
                    "Use HIGH only for materially dangerous or unusually one-sided terms, MEDIUM for terms needing attention, "
                    "and LOW for ordinary or low-impact terms. Do not invent facts or give definitive legal advice. Return JSON."
                ),
            },
            {"role": "user", "content": json.dumps(prompt_chunks)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "RiskAnalysisResponse",
                "schema": RiskAnalysisResponse.model_json_schema(),
            },
        },
        temperature=0.1,
    )
    generated = RiskAnalysisResponse.model_validate_json(completion.choices[0].message.content)

    for result in generated.clauses:
        cached_by_chunk[result.chunk_id] = {
            "chunk_id": result.chunk_id,
            "explanation_easy": result.explanation_easy,
            "risk_level": result.risk_level,
            "counter_offer": result.counter_offer,
            "market_standard": result.market_standard,
        }
        supabase.table("clause_analysis").insert(cached_by_chunk[result.chunk_id]).execute()

    return _build_response(chunks, cached_by_chunk, category_by_id)


def _build_response(chunks: list[dict], analyses: dict, category_by_id: dict) -> dict:
    clauses = []
    for chunk in chunks:
        analysis = analyses.get(chunk["id"])
        if not analysis:
            continue
        clauses.append(
            ClauseRisk(
                chunk_id=chunk["id"],
                category=category_by_id.get(chunk.get("classification_id"), "Unclassified"),
                excerpt=chunk["text"][:280],
                risk_level=analysis["risk_level"],
                explanation_easy=analysis["explanation_easy"],
                counter_offer=analysis.get("counter_offer"),
                market_standard=analysis.get("market_standard"),
            )
        )

    counts = {level: sum(item.risk_level == level for item in clauses) for level in ("LOW", "MEDIUM", "HIGH")}
    overall = "HIGH" if counts["HIGH"] else "MEDIUM" if counts["MEDIUM"] else "LOW"
    return RiskAnalysisResponse(
        overall_risk=overall,
        high_risk_count=counts["HIGH"],
        medium_risk_count=counts["MEDIUM"],
        low_risk_count=counts["LOW"],
        clauses=clauses,
    ).model_dump()