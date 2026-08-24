from rank_bm25 import BM25Okapi
from rag.retrieval.model import RetrievedChunk

import re

def tokenize(text: str) -> list[str]:
    return re.findall(
        r"\b[\w\-]+\b",
        text.lower()
    )
class BM25Retriever:

    def __init__(self, chunks):
        self.chunks=chunks
        tokenized_chunks= [tokenize(chunk.text) for chunk in self.chunks]
        self.index= BM25Okapi(tokenized_chunks)


    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter=None
    ):

        query_tokens = tokenize(query)

        scores = self.index.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]


        results = []

        for rank, idx in enumerate(ranked_indices, start=1):

            chunk = self.chunks[idx]

            metadata = {
                "source": chunk.source,
                "file_type": chunk.file_type,
                "chunk_index": chunk.chunk_index,
                "chunking_strategy": chunk.chunking_strategy,
                **chunk.metadata
            }

            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    metadata=metadata,
                    score=scores[idx],
                    rank=rank
                )
            )

        return results
