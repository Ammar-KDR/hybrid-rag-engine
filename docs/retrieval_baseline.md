# Dense Retrieval Baseline

## Configuration

Embedding:
sentence-transformers/all-MiniLM-L6-v2

Vector database:
Qdrant

Chunks:
54

Evaluation queries:
20

top_k:
5


## Metrics

Hit Rate@5:
0.90

Recall@5:
0.88

Precision@5:
0.19

MRR@5:
0.80


## Observations

- Dense retrieval successfully finds relevant evidence.
- Ranking quality is strong.
- Precision is lower because the retriever returns related chunks.
- Future improvements:
    - hybrid retrieval
    - reranking
    - query expansion