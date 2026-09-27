# Evaluation Results

## OVERALL RETRIEVAL PERFORMANCE
| Method | Recall@5 | Recall@10 | MRR | CRR |
| :--- | :--- | :--- | :--- | :--- |
| Standard RAG | 0.86 | 0.86 | 0.73 | 0.24 |
| 1-Hop Cross-Ref RAG | **0.86** | **0.88** | **0.73** | **0.39** |

## TABLE III: PERFORMANCE BY QUERY CATEGORY
| Query Type | Standard RAG | 1-Hop RAG | Improvement |
| :--- | :--- | :--- | :--- |
| Direct | 0.89 (MRR) | 0.89 (MRR) | 0.00 |
| 1-Hop Dependent | 0.50 (CRR) | **0.82 (CRR)** | **+0.32** |

## TABLE IV: DOWNSTREAM ANSWER QUALITY
| Method | Answer Accuracy | Faithfulness |
| :--- | :--- | :--- |
| Standard RAG | 0.98 | 1.00 |
| 1-Hop Cross-Ref RAG | **0.98** | **0.97** |

## TABLE V: AVERAGE RESPONSE TIME (SECONDS)
| Query Type | Standard RAG | 1-Hop RAG |
| :--- | :--- | :--- |
| Direct | 2.31 | 2.73 |
| 1-Hop Dependent | 2.24 | 2.71 |
