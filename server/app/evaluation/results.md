# Evaluation Results

> **Evaluation Design:** Standard RAG uses top-5 chunks (realistic LLM context budget).
> 1-Hop Cross-Ref RAG also fetches top-5 primary chunks, then adds cross-referenced clauses
> via the legal citation graph. Both have the **same primary retrieval budget**.
> The advantage of 1-Hop RAG lies in **targeted graph expansion**, not brute-force retrieval.

## TABLE I: CROSS-REFERENCE RECOVERY (KEY DIFFERENTIATOR)
| Method | Cross-Refs Missed | Recovered by Expansion | CRR (1-Hop Dep.) |
| :--- | :--- | :--- | :--- |
| Standard RAG (k=5) | 3 / 12 | — | 0.75 |
| 1-Hop Cross-Ref RAG | 0 / 12 | 3 newly recovered | **1.00** |

## TABLE II: OVERALL RETRIEVAL PERFORMANCE
| Method | Recall@5 | Recall@10 | MRR | CRR |
| :--- | :--- | :--- | :--- | :--- |
| Standard RAG | 0.96 | 0.96 | 0.84 | 0.16 |
| 1-Hop Cross-Ref RAG | **0.96** | **0.96** | **0.84** | **0.21** |

## TABLE III: PERFORMANCE BY QUERY CATEGORY
| Query Type | Standard RAG (MRR) | 1-Hop RAG (MRR) | Standard RAG (CRR) | 1-Hop RAG (CRR) | Improvement (CRR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Direct | 0.89 | 0.89 | N/A | N/A | N/A |
| 1-Hop Dependent | 0.65 | 0.65 | 0.75 | **1.00** | +0.25 |

## TABLE IV: DOWNSTREAM ANSWER QUALITY
| Method | Answer Accuracy | Faithfulness |
| :--- | :--- | :--- |
| Standard RAG | 0.98 | 1.00 |
| 1-Hop Cross-Ref RAG | **0.98** | **0.97** |

## TABLE V: AVERAGE RESPONSE TIME (SECONDS)
| Query Type | Standard RAG | 1-Hop RAG |
| :--- | :--- | :--- |
| Direct | 2.63 | 76.49 |
| 1-Hop Dependent | 2.60 | 3.45 |
