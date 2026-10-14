# Evaluation Results

## OVERALL RETRIEVAL PERFORMANCE
| Method | Recall@5 | Complete Chain Recall | MRR | CRR |
| :--- | :--- | :--- | :--- | :--- |
| Standard RAG | 0.87 | 0.47 | 0.71 | 0.55 |
| 1-Hop Cross-Ref RAG | **0.87** | **0.80** | **0.71** | **0.85** |

## TABLE III: PERFORMANCE BY QUERY CATEGORY
| Query Type | Standard RAG | 1-Hop RAG | Improvement |
| :--- | :--- | :--- | :--- |
| Direct | 0.89 (MRR) | 0.89 (MRR) | 0.0% (+0.00) |
| 1-Hop Dependent | 0.55 (CRR) | **0.85 (CRR)** | **+56.7% (+0.31)** |

## TABLE IV: DOWNSTREAM ANSWER QUALITY
| Method | Answer Accuracy | Faithfulness |
| :--- | :--- | :--- |
| Standard RAG | 0.98 | 1.00 |
| 1-Hop Cross-Ref RAG | **0.98** | **0.97** |

## TABLE V: AVERAGE RESPONSE TIME (SECONDS)
| Query Type | Standard RAG | 1-Hop RAG |
| :--- | :--- | :--- |
| Direct | 2.07 | 2.59 |
| 1-Hop Dependent | 2.23 | 2.88 |
