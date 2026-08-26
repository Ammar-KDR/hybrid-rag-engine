from dataclasses import dataclass

@dataclass
class RerankedChunk:
    chunk_id: str
    text: str
    metadata: dict

    retrieval_score: float
    retrieval_rank: int

    reranker_score: float
    reranked_rank: int
    final_score: float
    final_rank : int