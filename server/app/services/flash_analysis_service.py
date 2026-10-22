import logging
import os
import json
import time
from groq import Groq
from app.schemas.flash_analysis import FlashAnalysisReport

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Context limit guard — rough token estimate (1 token ≈ 4 characters).
# gpt-oss-120b supports 128 k tokens; we leave a safe buffer for the
# system prompt + response (≈ 8 k tokens), so we allow ~120 k tokens
# of document context = ~480 000 characters.
# -----------------------------------------------------------------------
MAX_CONTEXT_CHARS = 480_000


def generate_flash_analysis(document_context: str, document_id: str) -> dict:
    """
    Sends the full ordered document context to gpt-oss-120b and returns
    a structured FlashAnalysisReport as a plain Python dictionary.

    Args:
        document_context: All chunk texts joined in chunk_no order.
        document_id:      Used only for logging (never sent to the LLM).

    Returns:
        A dictionary matching FlashAnalysisReport's structure.
    """

    # ── 1. Context-limit guard ──────────────────────────────────────────
    if len(document_context) > MAX_CONTEXT_CHARS:
        logger.warning(
            f"[FLASH_SERVICE] Document {document_id} exceeds context limit "
            f"({len(document_context)} chars > {MAX_CONTEXT_CHARS} chars). Rejecting."
        )
        raise ValueError(
            "Document is too large for Flash Analysis in this version. "
            "The document context exceeds the model's safe context limit."
        )

    # ── 2. Build the system prompt ──────────────────────────────────────
    system_prompt = """You are an elite Legal AI analyst. A user has uploaded a legal document and needs to understand it before deciding whether to sign it. You will receive the complete document text below.

Your job is to produce a clear, structured Flash Analysis report that a person with no legal training can understand and act on.

---

## INSTRUCTIONS

### A. Understand the entire document first
Read the full document before writing anything. Understand its purpose, parties, definitions, key terms, obligations, conditions, exceptions, dates and schedules. Do NOT summarize clauses in isolation.

### B. Categorize the clauses
Group related clauses into relevant categories based on the actual document. Use only categories that apply. Possible categories include (not limited to):
- Financial obligations and payments
- Rights and responsibilities
- Termination and renewal
- Liability and indemnification
- Confidentiality and data protection
- Intellectual property
- Restrictions and penalties
- Dispute resolution and governing law
Create other categories when the document requires them.

### C. Analyze every relevant category
For each category:
- Explain important clauses in simple English (no jargon, or explain jargon when used).
- Identify provisions that favor or protect the user.
- Identify unfavorable provisions and potential risks.
- State each party's obligations.
- Mention clause numbers or references from the document text.
Do NOT invent findings to fill the report.

### D. Analyze cross-references
Identify relationships between clauses. If one clause qualifies or creates an exception to another, explain the combined practical effect. Do NOT claim clauses conflict merely because they discuss similar topics.

### E. Identify risks and warnings
Identify the most important risks for the user based on:
- Financial consequences
- Legal obligations and penalties
- Termination rights
- Unusual or restrictive conditions
- Ambiguous or missing terms
Prioritize by severity. Do NOT treat every clause as equally risky.

### F. Overall verdict
Give a clear, honest overall assessment. Choose one that fits:
- "Generally reasonable based on the available text"
- "Proceed with caution"
- "Significant concerns require clarification"
- "Not advisable to sign without resolving critical issues"
Explain the main reasons. Never base the verdict on clause count alone.
If the document is incomplete or cannot determine the user's position, state that limitation clearly.

### G. Practical next steps (Before You Sign)
List the most important questions, terms to clarify or negotiate, and conditions to verify before signing. Explain briefly why each matters. Order by importance.

### H. Writing style
- Simple, direct English only.
- Explain legal terms when used.
- No unnecessary jargon, repetition, or generic disclaimers.
- Be concise but never omit material information.
- Do NOT assume the user is a specific party (tenant, employee, buyer, etc.) unless it is evident from the document.
- Do NOT invent dates, amounts, penalties, obligations, or clause references.
- Every finding must be supported by the document. State limitations when source text is missing or unclear.

---

## OUTPUT FORMAT
Return ONLY a valid JSON object matching this exact schema — no prose before or after the JSON:

{
  "overall_verdict": "<short assessment with main reasons>",
  "document_overview": "<document purpose, parties, and main contractual arrangement>",
  "category_analysis": [
    {
      "category": "<category name>",
      "key_clauses": "<plain English explanation of important clauses in this category>",
      "favorable_terms": "<what protects or benefits the user>",
      "risks": "<what could hurt the user>",
      "obligations": "<what each party must do>",
      "clause_references": "<clause/section numbers or headings from the document>"
    }
  ],
  "important_warnings": [
    {
      "title": "<short warning title>",
      "detail": "<explanation of the risk and its consequence>"
    }
  ],
  "before_you_sign": [
    "<action item 1>",
    "<action item 2>"
  ]
}"""

    # ── 3. Call the LLM ─────────────────────────────────────────────────
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

    logger.info(f"[FLASH_SERVICE] Sending document {document_id} to gpt-oss-120b...")
    llm_start = time.time()

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"DOCUMENT TEXT:\n\n{document_context}"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "FlashAnalysisReport",
                "schema": FlashAnalysisReport.model_json_schema()
            }
        },
        temperature=0.2,
        timeout=300  # 5-minute timeout for large documents
    )

    llm_duration = round(time.time() - llm_start, 2)
    logger.info(f"[FLASH_SERVICE] LLM response received for document {document_id} in {llm_duration}s.")

    # ── 4. Parse and return ─────────────────────────────────────────────
    raw_content = completion.choices[0].message.content
    report = json.loads(raw_content)
    return report
