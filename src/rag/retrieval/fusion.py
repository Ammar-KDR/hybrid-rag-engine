from collections import defaultdict

from .model import RetrievedChunk

class  ReciprocalRankFusion:
    def __init__(self, k: int = 60): # k here is the smoothing parameter
        self.k = k

    def fuse(
        self,
        rankings: dict[str, list[RetrievedChunk]]
    ) -> list[RetrievedChunk]:
        scores = defaultdict(float) # stores the scores of each chunk , ex : {"abcd":0.89}
        chunks = {} #stores the updates chunk ex: {"abcd":RetrievedChunk() }
        retrieval_metadata = defaultdict(dict)

        for retriever_name , results in rankings.items():
            for rank , chunk in enumerate(results,start=1):
                rrf=1/(self.k+rank)
                scores[chunk.chunk_id]+=rrf
                chunks[chunk.chunk_id] = chunk
                retrieval_metadata[chunk.chunk_id][retriever_name]= {
                    "rank":rank,
                    "score":float(chunk.score)
                    }
        sorted_chunks = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
        )
        final_results = []

        for final_rank, (chunk_id, rrf_score) in enumerate(
            sorted_chunks,
            start=1
        ):
            chunk = chunks[chunk_id]

            metadata = {
                **chunk.metadata,
                "retrieval": {
                    "fusion": "rrf",
                    "rrf_score": rrf_score,
                    "sources": retrieval_metadata[chunk_id],
                }
            }

            final_results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    metadata=metadata,
                    score=float(rrf_score),
                    rank=final_rank,
                )
            )
        return final_results
                    
                    

