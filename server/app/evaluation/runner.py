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

def run_evaluation(evaluate_generation: bool = True):
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    results = []

    print(f"\n--- Running Evaluation on {len(dataset)} Questions ---")
    for i, item in enumerate(dataset, 1):
        doc_id = item["document_id"]
        question = item["question"]
        gold_nos = item["gold_chunk_nos"]
        gold_ref_no = item["gold_referenced_chunk_no"]
        ref_answer = item["reference_answer"]
        q_type = item["query_type"]

        print(f"[{i}/{len(dataset)}] Evaluating ({q_type}): {question[:60]}...")

        # Run Standard RAG (use_1hop_expansion = False)
        std_res = answer_question(doc_id, question, use_1hop_expansion=False, generate_answer=evaluate_generation)
        std_primary = std_res.get("primary_clauses", [])
        std_retrieved = [c["chunk_no"] for c in std_primary]
        std_context = "\n".join([c["text"] for c in std_primary])
        
        # Polite delay to avoid Groq TPM rate limits if using Groq cloud
        if evaluate_generation and get_llm_provider() == "groq":
            time.sleep(2)

        # Run 1-Hop RAG (use_1hop_expansion = True)
        hop_res = answer_question(doc_id, question, use_1hop_expansion=True, generate_answer=evaluate_generation)
        hop_primary = hop_res.get("primary_clauses", [])
        hop_expanded = hop_res.get("expanded_clauses", [])
        
        hop_primary_retrieved = [c["chunk_no"] for c in hop_primary]
        hop_retrieved = list(dict.fromkeys(
            hop_primary_retrieved + [c["chunk_no"] for c in hop_expanded]
        ))
        
        hop_all_clauses = hop_primary + hop_expanded
        hop_context = "\n".join([c["text"] for c in hop_all_clauses])
        
        if evaluate_generation and get_llm_provider() == "groq":
            time.sleep(2)

        std_metrics = {
            "recall_5": calculate_recall_at_k(std_retrieved, gold_nos, 5),
            "recall_10": calculate_recall_at_k(std_retrieved, gold_nos, 10),
            "mrr": calculate_mrr(std_retrieved, gold_nos),
            "crr": calculate_crr(std_retrieved, gold_ref_no),
            "accuracy": evaluate_answer_accuracy(std_res.get("answer", ""), ref_answer) if evaluate_generation else 0.0,
            "faithfulness": evaluate_faithfulness(std_res.get("answer", ""), std_context) if evaluate_generation else 0.0
        }

        hop_metrics = {
            "recall_5": calculate_recall_at_k(hop_primary_retrieved, gold_nos, 5),
            "recall_10": calculate_recall_at_k(hop_primary_retrieved, gold_nos, 10),
            "mrr": calculate_mrr(hop_primary_retrieved, gold_nos),
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
            "std": std_metrics,
            "hop": hop_metrics
        })

    # Save detailed per-question results to JSON
    results_json = os.path.join(os.path.dirname(__file__), "results_per_question.json")
    with open(results_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nPer-question detailed results saved to {results_json}")

    # Aggregate
    def avg(metrics_list, key):
        values = [m[key] for m in metrics_list if m.get(key) is not None]
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
| Method | Recall@5 | Recall@10 | MRR | CRR | Avg. Retrieved Chunks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Standard RAG | {avg(std_all, 'recall_5'):.2f} | {avg(std_all, 'recall_10'):.2f} | {avg(std_all, 'mrr'):.2f} | {avg(std_all, 'crr'):.2f} | {avg_std_chunks:.2f} |
| 1-Hop Cross-Ref RAG | **{avg(hop_all, 'recall_5'):.2f}** | **{avg(hop_all, 'recall_10'):.2f}** | **{avg(hop_all, 'mrr'):.2f}** | **{avg(hop_all, 'crr'):.2f}** | **{avg_final:.2f}** |

## TABLE III: PERFORMANCE BY QUERY CATEGORY
| Query Type | Standard MRR | 1-Hop MRR | Standard CRR | 1-Hop CRR |
| :--- | :--- | :--- | :--- | :--- |
| Direct | {avg(std_direct, 'mrr'):.2f} | {avg(hop_direct, 'mrr'):.2f} | N/A | N/A |
| 1-Hop Dependent | {avg(std_dep, 'mrr'):.2f} | {avg(hop_dep, 'mrr'):.2f} | {avg(std_dep, 'crr'):.2f} | **{avg(hop_dep, 'crr'):.2f}** |

## TABLE IV: 1-HOP CROSS-REFERENCE RECOVERY AUDIT (35 Dependent Queries)
| Metric | Count | Percentage |
| :--- | :--- | :--- |
| Total Cross-Reference Target Clauses | {len(dep_questions)} | 100.0% |
| Already Present in Standard Top-5 | {already_in_std} | {already_in_std / len(dep_questions) * 100:.1f}% |
| Missed by Standard Top-5 Vector Search | {missed_by_std} | {missed_by_std / len(dep_questions) * 100:.1f}% |
| **Newly Recovered by 1-Hop Graph Expansion** | **{recovered_by_hop}** | **{recovered_by_hop / len(dep_questions) * 100:.1f}%** |
| Unrecovered Targets | {not_recovered} | {not_recovered / len(dep_questions) * 100:.1f}% |

## TABLE V: DOWNSTREAM ANSWER QUALITY
| Method | Answer Accuracy | Faithfulness |
| :--- | :--- | :--- |
| Standard RAG | {avg(std_all, 'accuracy'):.2f} | {avg(std_all, 'faithfulness'):.2f} |
| 1-Hop Cross-Ref RAG | **{avg(hop_all, 'accuracy'):.2f}** | **{avg(hop_all, 'faithfulness'):.2f}** |
"""

    results_file = os.path.join(os.path.dirname(__file__), "results.md")
    with open(results_file, "w") as f:
        f.write(md_output)
        
    print(md_output)
    print(f"Results saved to {results_file}")

if __name__ == "__main__":
    run_evaluation()
