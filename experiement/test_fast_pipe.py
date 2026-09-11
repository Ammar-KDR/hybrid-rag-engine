from contextlib import asynccontextmanager

from fastapi import FastAPI , Depends
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel, field_validator

from rag.factory import create_rag_pipeline
from rag.pipeline import RAGPipeline

from typing import Optional

class AskRequest(BaseModel):
    question: str
    trace:bool=True

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Question must not be empty.")

        return cleaned



class CitationResponse(BaseModel):
    reference: int
    chunk_id: str
    source: str
    page_number: Optional[int] = None
    heading_path: list[str]


class LatencyResponse(BaseModel):
    retrieval_ms: float
    reranking_ms: float
    generation_ms: float
    verification_ms: float
    total_ms: float


class TokenUsageResponse(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

class ClaimResponse(BaseModel):
    text: str
    citations: list[int]


class CitationVerificationResponse(BaseModel):
    claim_text: str
    reference: int
    verdict: str
    explanation: str


class CitationMetricsResponse(BaseModel):
    citation_precision: float
    citation_coverage: float

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
    citation_verification: list[CitationVerificationResponse]
    citation_metrics: CitationMetricsResponse
    faithfulness: FaithfulnessResponse
    abstention: AbstentionResponse



class RankingStageResponse(BaseModel):
    rank: Optional[int] = None
    score: Optional[float] = None

class RetrievalCandidateResponse(BaseModel):
    chunk_id: str
    source: Optional[str] = None
    text: str

    rrf: RankingStageResponse
    dense: Optional[RankingStageResponse] = None
    bm25: Optional[RankingStageResponse] = None

class RerankedChunkResponse(BaseModel):
    chunk_id: str
    source: Optional[str] = None
    text: str

    retrieval: RankingStageResponse
    reranker: RankingStageResponse
    final: RankingStageResponse

class RetrievalTraceResponse(BaseModel):
    candidate_count: int
    evidence_count: int

    candidates: list[RetrievalCandidateResponse]
    final_evidence: list[RerankedChunkResponse]


class AskResponse(BaseModel):
    question: str
    answer: str
    abstained: bool

    citations: list[CitationResponse]

    verification: VerificationResponse

    latency: LatencyResponse
    token_usage: TokenUsageResponse
    trace: RetrievalTraceResponse | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline = create_rag_pipeline()

    app.state.rag_pipeline = pipeline

    yield

app = FastAPI(lifespan=lifespan)

def get_rag_pipeline(request: Request) -> RAGPipeline:
    return request.app.state.rag_pipeline

#@app.post("/v1/ask")
#def ask(request_body:AskRequest , pipeline: RAGPipeline =Depends(get_rag_pipeline)):
    result=pipeline.run(request_body.question)


@app.post("/v1/ask", response_model=AskResponse)
def ask(
    request_body: AskRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    result = pipeline.run(request_body.question)

    verified = result.verified_answer
    generated = result.answer
    claims = [
        ClaimResponse(
            text=claim.text,
            citations=claim.citations,
        )
        for claim in verified.claims.claims
    ]

    citations = [
        CitationResponse(
            reference=citation.reference,
            chunk_id=citation.chunk_id,
            source=citation.source,
            page_number=citation.page_number,
            heading_path=citation.heading_path,
        )
        for citation in generated.citations
    ]
    citation_verifications = [
        CitationVerificationResponse(
            claim_text=item.claim_text,
            reference=item.reference,
            verdict=item.verdict.value,
            explanation=item.explanation,
        )
        for item in verified.citation_verification.verifications
    ]

    metrics = verified.citation_metrics

    citation_metrics = CitationMetricsResponse(
        citation_precision=metrics.citation_precision,
        citation_coverage=metrics.citation_coverage,

        total_verifications=metrics.total_verifications,
        supported_verifications=metrics.supported_verifications,
        partially_supported_verifications=metrics.partially_supported_verifications,
        unsupported_verifications=metrics.unsupported_verifications,
        contradicted_verifications=metrics.contradicted_verifications,
    )

    faithfulness = verified.faithfulness
    faithfulness_response = FaithfulnessResponse(
        total_claims=faithfulness.total_claims,
        supported_claims=faithfulness.supported_claims,
        partially_supported_claims=faithfulness.partially_supported_claims,
        unsupported_claims=faithfulness.unsupported_claims,
        contradicted_claims=faithfulness.contradicted_claims,

        claims=[
            FaithfulnessClaimResponse(
                claim_text=item.claim_text,
                verdict=item.verdict.value,
                explanation=item.explanation,
            )
            for item in faithfulness.claim_results
        ],
    )
    abstention_response = AbstentionResponse(
        should_abstain=verified.abstention.should_abstain,
        decision=verified.abstention.decision.value,
        reasons=verified.abstention.reasons,
    )

    candidate_responses = []

    for candidate in result.candidates:
        retrieval = candidate.metadata.get("retrieval", {})
        sources = retrieval.get("sources", {})

        dense = sources.get("dense")
        bm25 = sources.get("bm25")

        candidate_responses.append(
            RetrievalCandidateResponse(
                chunk_id=candidate.chunk_id,
                source=candidate.metadata.get("source"),
                text=candidate.text,

                rrf=RankingStageResponse(
                    rank=candidate.rank,
                    score=candidate.score,
                ),

                dense=(
                    RankingStageResponse(
                        rank=dense.get("rank"),
                        score=dense.get("score"),
                    )
                    if dense
                    else None
                ),

                bm25=(
                    RankingStageResponse(
                        rank=bm25.get("rank"),
                        score=bm25.get("score"),
                    )
                    if bm25
                    else None
                ),
            )
        )
    reranked_responses = [
            RerankedChunkResponse(
                chunk_id=chunk.chunk_id,
                source=chunk.metadata.get("source"),
                text=chunk.text,

                retrieval=RankingStageResponse(
                    rank=chunk.retrieval_rank,
                    score=chunk.retrieval_score,
                ),

                reranker=RankingStageResponse(
                    rank=chunk.reranked_rank,
                    score=chunk.reranker_score,
                ),

                final=RankingStageResponse(
                    rank=chunk.final_rank,
                    score=chunk.final_score,
                ),
            )
            for chunk in result.reranked_chunks
        ]
    return AskResponse(
        question=request_body.question,
        answer=verified.final_answer,
        abstained=verified.abstention.should_abstain,

        citations=citations,

        latency=LatencyResponse(
            retrieval_ms=result.retrieval_latency_ms,
            reranking_ms=result.reranking_latency_ms,
            generation_ms=result.generation_latency_ms,
            verification_ms=result.verification_latency_ms,
            total_ms=result.total_latency_ms,
        ),
        verification=VerificationResponse(
            claims=claims,
            citation_verification=citation_verifications,
            citation_metrics=citation_metrics,
            faithfulness=faithfulness_response,
            abstention=abstention_response,
        ),

        token_usage=TokenUsageResponse(
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
            total_tokens=generated.total_tokens,
        ),
        trace=RetrievalTraceResponse(
            candidate_count=result.candidate_count,
            evidence_count=result.evidence_count,
            candidates=candidate_responses,
            final_evidence=reranked_responses,
        ) if request_body.trace else None,
    )