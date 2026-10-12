from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, field_validator

from rag.api.schemas.ask import EvidenceRef


class ComparisonRelationship(str, Enum):
    AGREEMENT = "agreement"
    POSSIBLE_CONFLICT = "possible_conflict"
    SCOPE_OR_VERSION_DIFFERENCE = "scope_or_version_difference"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class DocumentClaim(BaseModel):
    document_id: str
    filename: str
    claim: str
    evidence: list[EvidenceRef] = []
    scope_notes: Optional[str] = None


class CompareRequest(BaseModel):
    document_a_id: str
    document_b_id: str
    topic: str
    verification_mode: Literal["fast", "full"] = "fast"

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Topic must not be empty.")
        return cleaned


class CompareResponse(BaseModel):
    topic: str
    relationship: ComparisonRelationship
    summary: str
    document_a: DocumentClaim
    document_b: DocumentClaim
    resolution_notes: str
    confidence: Literal["high", "medium", "low"]
