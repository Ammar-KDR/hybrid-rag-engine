import re
from rank_bm25 import BM25Okapi
from rag.retrieval.model import RetrievedChunk
from rag.nlp.arabic import is_arabic_text, tokenize_arabic


def tokenize(text: str) -> list[str]:
    if is_arabic_text(text):
        return tokenize_arabic(text)
    return re.findall(
        r"\b[\w\-]+\b",
        text.lower()
    )
class BM25Retriever:

    def __init__(self, chunks: list | None = None):
        self.chunks = list(chunks) if chunks else []
        if self.chunks:
            tokenized_chunks = [tokenize(chunk.text) for chunk in self.chunks]
            self.index = BM25Okapi(tokenized_chunks)
        else:
            self.index = None

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter=None
    ):
        if not self.chunks or self.index is None:
            return []

        query_tokens = tokenize(query)
        scores = self.index.get_scores(query_tokens)

        if filter is not None and getattr(filter, "document_ids", None):
            target_ids = set(filter.document_ids)
            candidate_indices = [
                i for i, chunk in enumerate(self.chunks)
                if (
                    chunk.metadata.get("document_id") in target_ids
                    or getattr(chunk, "document_id", None) in target_ids
                    or chunk.metadata.get("doc_id") in target_ids
                    or getattr(chunk, "source", "") in target_ids
                )
            ]
        else:
            candidate_indices = list(range(len(scores)))

        ranked_indices = sorted(
            candidate_indices,
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
                "document_id": chunk.metadata.get("document_id") or getattr(chunk, "document_id", None),
                "filename": chunk.metadata.get("filename") or getattr(chunk, "filename", None),
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
