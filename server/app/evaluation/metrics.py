import re
import logging
from typing import List, Optional
from rouge_score import rouge_scorer

logger = logging.getLogger(__name__)

# Initialize ROUGE scorer
scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)


def calculate_recall_at_k(retrieved_chunk_nos: List[int], gold_chunk_nos: List[int], k: int) -> float:
    """Calculates Recall@k against gold clause chunk numbers."""
    if not gold_chunk_nos:
        return 0.0
    top_k = retrieved_chunk_nos[:k]
    hits = sum(1 for gold_no in gold_chunk_nos if gold_no in top_k)
    return hits / len(gold_chunk_nos)


def calculate_mrr(retrieved_chunk_nos: List[int], gold_chunk_nos: List[int]) -> float:
    """Calculates Mean Reciprocal Rank (MRR) for the first relevant chunk."""
    if not gold_chunk_nos:
        return 0.0
    for i, chunk_no in enumerate(retrieved_chunk_nos):
        if chunk_no in gold_chunk_nos:
            return 1.0 / (i + 1)
    return 0.0


def calculate_crr(retrieved_chunk_nos: List[int], gold_referenced_chunk_no: Optional[int]) -> float:
    """
    Calculates Cross-Reference Recall (CRR).
    Returns 1.0 if the cross-referenced target clause is retrieved, else 0.0.
    """
    if gold_referenced_chunk_no is None:
        return 0.0
    return 1.0 if gold_referenced_chunk_no in retrieved_chunk_nos else 0.0


def calculate_rouge_l(candidate: str, reference: str) -> float:
    """Calculates standard ROUGE-L F1 score between candidate answer and reference."""
    if not candidate or not reference:
        return 0.0
    scores = scorer.score(reference, candidate)
    return scores['rougeL'].fmeasure


def evaluate_faithfulness_llm(answer: str, retrieved_context: str) -> float:
    """
    LLM-as-a-Judge Faithfulness evaluation:
    Determines whether all factual claims in the answer can be directly inferred from the retrieved context.
    Returns float score between 0.0 and 1.0.
    """
    if not answer or not retrieved_context:
        return 0.0

    from app.core.llm import generate_chat_completion

    prompt = f"""You are an impartial evaluator assessing the faithfulness of a legal RAG answer.

Context:
{retrieved_context}

Answer:
{answer}

Evaluate whether the factual and legal claims in the answer are supported by the provided context.

Scoring rubric:
1.0 = All substantive claims are supported by the context.
0.75 = Mostly supported, with only minor unsupported details.
0.50 = Partially supported; some substantive claims are unsupported.
0.25 = Largely unsupported by the context.
0.0 = The answer is unsupported or contradicts the context.

Do not use outside knowledge.

Respond ONLY with a single JSON object in the exact format:
{{"score": <0.0, 0.25, 0.50, 0.75, or 1.0>, "reason": "<brief justification>"}}
"""
    try:
        response_text = generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=250
        )
        match = re.search(r'"score"\s*:\s*(0(?:\.\d+)?|1(?:\.0+)?)', response_text)
        if match:
            return float(match.group(1))
        match = re.search(r'score\s*[:=]\s*(0(?:\.\d+)?|1(?:\.0+)?)', response_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        logger.warning(f"Invalid faithfulness judge response: {response_text}")
        return None
    except Exception as e:
        logger.warning(f"Faithfulness evaluation failed: {e}")
        return None


def evaluate_correctness_llm(answer: str, reference_answer: str):
    """
    LLM-as-a-Judge Answer Correctness:
    Determines how accurately and completely the generated answer matches the reference answer.
    Returns float score between 0.0 and 1.0, or None if evaluation fails.
    """
    if not answer or not reference_answer:
        return None

    from app.core.llm import generate_chat_completion

    prompt = f"""You are an impartial evaluator assessing a generated legal answer against a reference answer.

Reference Answer:
{reference_answer}

Candidate Answer:
{answer}

Evaluate:
1. Legal/factual correctness
2. Completeness of the important information
3. Whether the candidate contradicts the reference

Note on citations: Citation formatting differences should not reduce the score when the underlying legal content is correct. However, incorrect or unsupported citations should be treated as an error.

Scoring rubric:
1.0 = Correct and complete.
0.75 = Correct with minor omissions.
0.50 = Partially correct or incomplete.
0.25 = Mostly incorrect or substantially incomplete.
0.0 = Incorrect or contradictory.

Respond ONLY with a single JSON object in the exact format:
{{"score": <0.0, 0.25, 0.50, 0.75, or 1.0>, "reason": "<brief justification>"}}
"""
    try:
        response_text = generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=250
        )
        # Try JSON format first
        match = re.search(r'"score"\s*:\s*(0(?:\.\d+)?|1(?:\.0+)?)', response_text)
        if match:
            return float(match.group(1))
        # Try plain score: X format
        match = re.search(r'score\s*[:=]\s*(0(?:\.\d+)?|1(?:\.0+)?)', response_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        logger.warning(f"Invalid correctness judge response: {response_text}")
        return None
    except Exception as e:
        logger.warning(f"Correctness evaluation failed: {e}")
        return None

# Backward and clean aliases
evaluate_faithfulness = evaluate_faithfulness_llm
evaluate_answer_accuracy = evaluate_correctness_llm
