from typing import Literal
from pydantic import BaseModel, field_validator

from rag.api.schemas.ask import EvidenceRef


class BriefRequest(BaseModel):
    document_ids: list[str]
    focus: str = "Executive Summary, Critical Policies, and Key Dates"
    max_findings: int = 8
    verification_mode: Literal["fast", "full"] = "fast"

    @field_validator("document_ids")
    @classmethod
    def validate_docs(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("document_ids must contain at least one document ID.")
        return value


class BriefFinding(BaseModel):
    title: str
    description: str
    category: Literal["policy", "technical", "compliance", "action_item"]
    evidence: list[EvidenceRef] = []


class BriefResponse(BaseModel):
    focus: str
    document_count: int
    executive_summary: str
    findings: list[BriefFinding]
    analyzed_documents: list[str]
