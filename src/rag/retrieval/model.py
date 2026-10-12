from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalFilter:
    document_ids: tuple[str, ...] = ()

    def matches_document(self, doc_id: str | None) -> bool:
        if not self.document_ids:
            return True
        return doc_id in self.document_ids


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float
    rank: int