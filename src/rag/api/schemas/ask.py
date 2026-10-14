from typing import Literal
from pydantic import BaseModel, field_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class EvidenceRef(BaseModel):
    reference: int
    chunk_id: str
    document_id: str | None = None
    service_id: str | None = None
    service_name: str | None = None
    section_type: str | None = None
    filename: str | None = None
    source: str
    text: str
    file_type: str | None = None
    page_number: int | None = None
    heading_path: list[str] | None = None
    final_score: float | None = None
    reranker_score: float | None = None


class AskRequest(BaseModel):
    question: str
    include_trace: bool = False
    history: list[ChatMessage] = []
    document_ids: list[str] | None = None
    service_ids: list[str] | None = None
    verification_mode: Literal["fast", "full"] = "fast"

    @field_validator("question")
    @classmethod
    def validate_question(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Question must not be empty."
            )

        return cleaned


class CitationResponse(BaseModel):
    reference: int
    chunk_id: str
    source: str
    page_number: int | None = None
    heading_path: list[str] | None


class LatencyResponse(BaseModel):
    retrieval_ms: float
    reranking_ms: float
    generation_ms: float
    verification_ms: float
    total_ms: float


class TokenUsageResponse(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ClaimResponse(BaseModel):
    text: str
    citations: list[int]


class CitationVerificationResponse(BaseModel):
    claim_text: str
    reference: int
    verdict: str
    explanation: str


class CitationMetricsResponse(BaseModel):
    citation_precision: float | None
    citation_coverage: float | None

    total_verifications: int
    supported_verifications: int
    partially_supported_verifications: int
    unsupported_verifications: int
    contradicted_verifications: int


class FaithfulnessClaimResponse(BaseModel):
    claim_text: str
    verdict: str
    explanation: str


class FaithfulnessResponse(BaseModel):
    total_claims: int
    supported_claims: int
    partially_supported_claims: int
    unsupported_claims: int
    contradicted_claims: int

    claims: list[FaithfulnessClaimResponse]


class AbstentionResponse(BaseModel):
    should_abstain: bool
    decision: str
    reasons: list[str]


class VerificationResponse(BaseModel):
    claims: list[ClaimResponse]

    citation_verification: list[
        CitationVerificationResponse
    ]

    citation_metrics: CitationMetricsResponse
    faithfulness: FaithfulnessResponse
    abstention: AbstentionResponse


class RankingStageResponse(BaseModel):
    rank: int | None = None
    score: float | None = None


class RetrievalCandidateResponse(BaseModel):
    chunk_id: str
    source: str | None = None
    text: str

    rrf: RankingStageResponse
    dense: RankingStageResponse | None = None
    bm25: RankingStageResponse | None = None


class RerankedChunkResponse(BaseModel):
    chunk_id: str
    source: str | None = None
    text: str

    retrieval: RankingStageResponse
    reranker: RankingStageResponse
    final: RankingStageResponse


class RetrievalTraceResponse(BaseModel):
    candidate_count: int
    evidence_count: int

    candidates: list[
        RetrievalCandidateResponse
    ]

    final_evidence: list[
        RerankedChunkResponse
    ]


class AskResponse(BaseModel):
    request_id: str
    question: str
    original_question: str | None = None
    retrieval_question: str | None = None
    was_rewritten: bool = False
    answer: str
    abstained: bool

    citations: list[CitationResponse]
    evidence: list[EvidenceRef] = []

    verification: VerificationResponse

    latency: LatencyResponse
    token_usage: TokenUsageResponse
    selected_service_id: str | None = None
    selected_service_name: str | None = None

    trace: RetrievalTraceResponse | None = None