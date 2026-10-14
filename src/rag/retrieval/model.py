from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalFilter:
    document_ids: tuple[str, ...] = ()
    service_ids: tuple[str, ...] = ()

    def matches_document(self, doc_id: str | None) -> bool:
        if not self.document_ids:
            return True
        return doc_id in self.document_ids

    def matches_service(self, service_id: str | None) -> bool:
        if not self.service_ids:
            return True
        return service_id in self.service_ids

    def matches(self, doc_id: str | None = None, service_id: str | None = None) -> bool:
        return self.matches_document(doc_id) and self.matches_service(service_id)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float
    rank: int