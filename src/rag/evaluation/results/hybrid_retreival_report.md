# Retrieval Benchmark Results

Dataset:
hybrid_retrieval_golden.json

Corpus:
268 chunks

## Candidate Recall

| Retriever | Recall@20 |
|---|---:|
| Dense | 1.00 |
| Hybrid | 1.00 |

## Final Retrieval

| Architecture | Hit@5 | Recall@5 | MRR@5 | Latency |
|-|-:|-:|-:|-:|
| Dense | 0.96 | 0.94 | 0.68 | 23.51ms |
| BM25 | 0.88 | 0.88 | 0.52 | 0.43ms |
| Hybrid | 0.92 | 0.92 | 0.67 | 22.95ms |
| Hybrid + Reranker | 0.96 | 0.96 | 0.60 | 204.41ms |