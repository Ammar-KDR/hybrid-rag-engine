from rag.retrieval.model import RetrievedChunk
from .model import RerankedChunk

class CrossEncoderReranker:

    def __init__(self, model):
        self.model = model

    def rerank(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RerankedChunk]:

        # validation
        if not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <=0:
            raise ValueError("top_k must be greater than 0")
        if len(candidates)==0:
            return []

        # build (query, chunk) pairs

        query_chunk_pairs=[]
        for candidate in candidates:
            query_chunk_pairs.append((query, candidate.text))


        # model.predict(...)
        relevant_scores=self.model.predict(query_chunk_pairs)
            
        # associate candidates with scores
        candidates_scores=list(zip(candidates,relevant_scores))

        # sort highest score first
        candidates_scores.sort(key=lambda x: x[1], reverse=True)
        
        # convert to RerankedChunk
        Reranked_chunks=[]
        for rank,(cand, score) in enumerate(candidates_scores, start=1):
            rc=RerankedChunk(
        chunk_id=cand.chunk_id,
        text=cand.text,
        metadata=cand.metadata,
        retrieval_score=cand.score,
        retrieval_rank=cand.rank,
        reranker_score=float(score),
        reranked_rank=rank,
        final_score = float(score),
        final_rank = rank

            )
            Reranked_chunks.append(rc)
            

        # return top_k
        return Reranked_chunks[:top_k]