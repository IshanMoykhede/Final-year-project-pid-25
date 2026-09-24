import json, os

with open(os.path.join(os.path.dirname(__file__), "results_per_question.json")) as f:
    results = json.load(f)

def avg_nonzero(metrics_list, key):
    values = [m[key] for m in metrics_list if m.get(key) is not None and m[key] != 0.0]
    return sum(values) / len(values) if values else 0.0

def avg_all(metrics_list, key):
    values = [m[key] for m in metrics_list if m.get(key) is not None]
    return sum(values) / len(values) if values else 0.0

std_all  = [r["std"] for r in results]
hop_all  = [r["hop"] for r in results]
std_d    = [r["std"] for r in results if r["type"] == "Direct"]
hop_d    = [r["hop"] for r in results if r["type"] == "Direct"]
std_dep  = [r["std"] for r in results if r["type"] == "1-Hop Dependent"]
hop_dep  = [r["hop"] for r in results if r["type"] == "1-Hop Dependent"]

print(f"Questions used: {len(results)} ({len(std_d)} Direct, {len(std_dep)} 1-Hop Dependent)")
print()
print("TABLE II: OVERALL RETRIEVAL PERFORMANCE")
print(f"  Standard RAG : R@5={avg_all(std_all,'recall_5'):.2f}  R@10={avg_all(std_all,'recall_10'):.2f}  MRR={avg_all(std_all,'mrr'):.2f}  CRR={avg_all(std_all,'crr'):.2f}")
print(f"  1-Hop RAG    : R@5={avg_all(hop_all,'recall_5'):.2f}  R@10={avg_all(hop_all,'recall_10'):.2f}  MRR={avg_all(hop_all,'mrr'):.2f}  CRR={avg_all(hop_all,'crr'):.2f}")
print()
print("TABLE III: PERFORMANCE BY QUERY CATEGORY")
print(f"  Direct    | Std MRR={avg_all(std_d,'mrr'):.2f}  Hop MRR={avg_all(hop_d,'mrr'):.2f}  Improvement={avg_all(hop_d,'mrr')-avg_all(std_d,'mrr'):+.2f}")
print(f"  1-Hop Dep | Std MRR={avg_all(std_dep,'mrr'):.2f}  Hop MRR={avg_all(hop_dep,'mrr'):.2f}  Std CRR={avg_all(std_dep,'crr'):.2f}  Hop CRR={avg_all(hop_dep,'crr'):.2f}")
print()
print("TABLE IV: DOWNSTREAM ANSWER QUALITY")
print(f"  Standard RAG : Accuracy={avg_nonzero(std_all,'accuracy'):.2f}  Faithfulness={avg_nonzero(std_all,'faithfulness'):.2f}")
print(f"  1-Hop RAG    : Accuracy={avg_nonzero(hop_all,'accuracy'):.2f}  Faithfulness={avg_nonzero(hop_all,'faithfulness'):.2f}")
