import os
import json
import time
import logging
from app.core.llm import get_llm_provider
from app.services.chat_service import answer_question
from app.evaluation.metrics import (
    calculate_recall_at_k, calculate_mrr, calculate_crr,
    evaluate_faithfulness, evaluate_answer_accuracy
)

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_evaluation(evaluate_generation: bool = True, start_from: int = None):
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    # Load existing results to append to if resuming mid-way
    results_json = os.path.join(os.path.dirname(__file__), "results_per_question.json")
    if os.path.exists(results_json):
        with open(results_json, "r") as f:
            results = json.load(f)
        if start_from is None:
            start_from = len(results) + 1
        logger.info(f"Loaded {len(results)} existing results. Resuming from question {start_from}...")
    else:
        results = []
        if start_from is None:
            start_from = 1

    # Slice dataset to only process from start_from onwards
    dataset_to_process = dataset[start_from - 1:]

    print(f"\n--- Running Evaluation on {len(dataset_to_process)} Questions (starting from #{start_from} of {len(dataset)}) ---")
    for i, item in enumerate(dataset_to_process, start_from):
        doc_id = item["document_id"]
        question = item["question"]
        gold_nos = item["gold_chunk_nos"]
        gold_ref_no = item["gold_referenced_chunk_no"]
        ref_answer = item["reference_answer"]
        q_type = item["query_type"]

        print(f"[{i}/{len(dataset)}] Evaluating ({q_type}): {question[:60]}...")

        # Run Standard RAG (use_1hop_expansion = False, top_k=5)
        # Standard RAG uses top_k=5 — a realistic LLM context budget.
        # This ensures CRR correctly exposes that std RAG cannot reliably
        # surface cross-referenced chunks without explicit graph expansion.
        t0 = time.time()
        std_res = answer_question(doc_id, question, use_1hop_expansion=False, generate_answer=evaluate_generation, top_k=5)
        std_time = time.time() - t0
        std_primary = std_res.get("primary_clauses", [])
        std_retrieved = [c["chunk_no"] for c in std_primary]
        std_context = "\n".join([c["text"] for c in std_primary[:5]])
        
        # Polite delay to avoid Groq TPM rate limits if using Groq cloud
        if evaluate_generation and get_llm_provider() == "groq":
            time.sleep(10)

        # Run 1-Hop Cross-Ref RAG (use_1hop_expansion = True, top_k=5 primary)
        # 1-Hop RAG also retrieves top_k=5 primary chunks (same budget as Standard RAG),
        # then augments via targeted cross-reference graph expansion.
        t0 = time.time()
        hop_res = answer_question(doc_id, question, use_1hop_expansion=True, generate_answer=evaluate_generation, top_k=5)
        hop_time = time.time() - t0
        hop_primary = hop_res.get("primary_clauses", [])
        hop_expanded = hop_res.get("expanded_clauses", [])
        
        hop_primary_retrieved = [c["chunk_no"] for c in hop_primary]
        hop_retrieved = list(dict.fromkeys(
            hop_primary_retrieved + [c["chunk_no"] for c in hop_expanded]
        ))
        
        hop_all_clauses = hop_primary[:5] + hop_expanded
        hop_context = "\n".join([c["text"] for c in hop_all_clauses])
        
        if evaluate_generation and get_llm_provider() == "groq":
            time.sleep(10)

        std_metrics = {
            # MRR and Recall measure how well the PRIMARY source clause is ranked
            "recall_5": calculate_recall_at_k(std_retrieved, gold_nos, 5),
            "recall_10": calculate_recall_at_k(std_retrieved, gold_nos, 10),
            "mrr": calculate_mrr(std_retrieved, gold_nos),
            # CRR measures whether the cross-referenced target clause was retrieved
            "crr": calculate_crr(std_retrieved, gold_ref_no),
            "accuracy": evaluate_answer_accuracy(std_res.get("answer", ""), ref_answer) if evaluate_generation else 0.0,
            "faithfulness": evaluate_faithfulness(std_res.get("answer", ""), std_context) if evaluate_generation else 0.0
        }

        hop_metrics = {
            # MRR and Recall measure how well the PRIMARY source clause is ranked
            "recall_5": calculate_recall_at_k(hop_primary_retrieved, gold_nos, 5),
            "recall_10": calculate_recall_at_k(hop_primary_retrieved, gold_nos, 10),
            "mrr": calculate_mrr(hop_primary_retrieved, gold_nos),
            # CRR uses the full hop_retrieved (primary + expanded) so cross-ref recovery is credited
            "crr": calculate_crr(hop_retrieved, gold_ref_no),
            "accuracy": evaluate_answer_accuracy(hop_res.get("answer", ""), ref_answer) if evaluate_generation else 0.0,
            "faithfulness": evaluate_faithfulness(hop_res.get("answer", ""), hop_context) if evaluate_generation else 0.0
        }

        # Check if newly recovered target
        newly_recovered = False
        if gold_ref_no is not None:
            newly_recovered = (gold_ref_no not in std_retrieved) and (gold_ref_no in hop_retrieved)

        # Expansion sizes
        num_primary = len(hop_primary_retrieved)
        num_expanded = len(hop_expanded)
        num_final = len(hop_retrieved)

        # Record detailed per-question data
        results.append({
            "question_id": i,
            "document_id": doc_id,
            "type": q_type,
            "question": question,
            "gold_chunks": gold_nos,
            "gold_referenced_chunk": gold_ref_no,
            "std_retrieved": std_retrieved,
            "hop_primary": hop_primary_retrieved,
            "hop_expanded": [c["chunk_no"] for c in hop_expanded],
            "hop_retrieved": hop_retrieved,
            "num_primary_chunks": num_primary,
            "num_expanded_chunks": num_expanded,
            "num_final_chunks": num_final,
            "newly_recovered": newly_recovered,
            "std_time": std_time,
            "hop_time": hop_time,
            "std": std_metrics,
            "hop": hop_metrics
        })

        # Save incrementally after every question so progress is never lost
        results_json = os.path.join(os.path.dirname(__file__), "results_per_question.json")
        with open(results_json, "w") as f:
            json.dump(results, f, indent=2)
        print(f"  [Saved {len(results)} results so far]")

    # Save detailed per-question results to JSON
    results_json = os.path.join(os.path.dirname(__file__), "results_per_question.json")
    with open(results_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nPer-question detailed results saved to {results_json}")

    # Aggregate
    def avg(metrics_list, key):
        values = [m[key] for m in metrics_list if m.get(key) is not None]
        return sum(values) / len(values) if values else 0.0

    def avg_time(q_type, key):
        values = [r[key] for r in results if r["type"] == q_type and r.get(key) is not None]
        return sum(values) / len(values) if values else 0.0

    std_all = [r["std"] for r in results]
    hop_all = [r["hop"] for r in results]

    std_direct = [r["std"] for r in results if r["type"] == "Direct"]
    hop_direct = [r["hop"] for r in results if r["type"] == "Direct"]
    
    std_dep = [r["std"] for r in results if r["type"] == "1-Hop Dependent"]
    hop_dep = [r["hop"] for r in results if r["type"] == "1-Hop Dependent"]

    dep_questions = [r for r in results if r["type"] == "1-Hop Dependent"]
    already_in_std = sum(1 for r in dep_questions if r["gold_referenced_chunk"] in r["std_retrieved"])
    missed_by_std = len(dep_questions) - already_in_std
    recovered_by_hop = sum(1 for r in dep_questions if r.get("newly_recovered"))
    not_recovered = missed_by_std - recovered_by_hop

    avg_std_chunks = sum(len(r["std_retrieved"]) for r in results) / len(results) if results else 0.0
    avg_primary = sum(r["num_primary_chunks"] for r in results) / len(results) if results else 0.0
    avg_expanded = sum(r["num_expanded_chunks"] for r in results) / len(results) if results else 0.0
    avg_final = sum(r["num_final_chunks"] for r in results) / len(results) if results else 0.0

    md_output = f"""# Evaluation Results

## TABLE II: OVERALL RETRIEVAL PERFORMANCE
| Method | Recall@5 | Recall@10 | MRR | CRR |
| :--- | :--- | :--- | :--- | :--- |
| Standard RAG | {avg(std_all, 'recall_5'):.2f} | {avg(std_all, 'recall_10'):.2f} | {avg(std_all, 'mrr'):.2f} | {avg(std_all, 'crr'):.2f} |
| 1-Hop Cross-Ref RAG | **{avg(hop_all, 'recall_5'):.2f}** | **{avg(hop_all, 'recall_10'):.2f}** | **{avg(hop_all, 'mrr'):.2f}** | **{avg(hop_all, 'crr'):.2f}** |

## TABLE III: PERFORMANCE BY QUERY CATEGORY
| Query Type | Standard RAG (MRR) | 1-Hop RAG (MRR) | Standard RAG (CRR) | 1-Hop RAG (CRR) | Improvement (MRR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Direct | {avg(std_direct, 'mrr'):.2f} | {avg(hop_direct, 'mrr'):.2f} | N/A | N/A | {avg(hop_direct, 'mrr') - avg(std_direct, 'mrr'):+.2f} |
| 1-Hop Dependent | {avg(std_dep, 'mrr'):.2f} | {avg(hop_dep, 'mrr'):.2f} | {avg(std_dep, 'crr'):.2f} | **{avg(hop_dep, 'crr'):.2f}** | {avg(hop_dep, 'mrr') - avg(std_dep, 'mrr'):+.2f} |

## TABLE IV: DOWNSTREAM ANSWER QUALITY
| Method | Answer Accuracy | Faithfulness |
| :--- | :--- | :--- |
| Standard RAG | {avg(std_all, 'accuracy'):.2f} | {avg(std_all, 'faithfulness'):.2f} |
| 1-Hop Cross-Ref RAG | **{avg(hop_all, 'accuracy'):.2f}** | **{avg(hop_all, 'faithfulness'):.2f}** |

## TABLE V: AVERAGE RESPONSE TIME (SECONDS)
| Query Type | Standard RAG | 1-Hop RAG |
| :--- | :--- | :--- |
| Direct | {avg_time('Direct', 'std_time'):.2f} | {avg_time('Direct', 'hop_time'):.2f} |
| 1-Hop Dependent | {avg_time('1-Hop Dependent', 'std_time'):.2f} | {avg_time('1-Hop Dependent', 'hop_time'):.2f} |
"""

    results_file = os.path.join(os.path.dirname(__file__), "results.md")
    with open(results_file, "w") as f:
        f.write(md_output)
        
    print(md_output)
    print(f"Results saved to {results_file}")

if __name__ == "__main__":
    run_evaluation(evaluate_generation=True)
