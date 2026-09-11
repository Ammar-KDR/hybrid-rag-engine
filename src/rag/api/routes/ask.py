import logging
import uuid

from fastapi import APIRouter, Depends

from rag.pipeline import RAGPipeline

from rag.api.dependencies import get_rag_pipeline
from rag.api.errors import AppError

from rag.api.schemas.ask import (
    AbstentionResponse,
    AskRequest,
    AskResponse,
    CitationMetricsResponse,
    CitationResponse,
    CitationVerificationResponse,
    ClaimResponse,
    FaithfulnessClaimResponse,
    FaithfulnessResponse,
    LatencyResponse,
    RankingStageResponse,
    RerankedChunkResponse,
    RetrievalCandidateResponse,
    RetrievalTraceResponse,
    TokenUsageResponse,
    VerificationResponse,
)
import logging
from openai import APIConnectionError


router = APIRouter()

logger = logging.getLogger(
    "rag.api.ask"
)


@router.post(
    "/ask",
    response_model=AskResponse,
)
def ask(
    request_body: AskRequest,
    pipeline: RAGPipeline = Depends(
        get_rag_pipeline
    ),
):
    request_id = str(uuid.uuid4())

    logger.info(
        "rag_request_started",
        extra={
            "request_id": request_id,
            "question": request_body.question,
        },
    )

    try:
        result = pipeline.run(
            request_body.question
        )

    
    except APIConnectionError as exc:

        logger.exception(
            "rag_model_unavailable",
            extra={
                "request_id": request_id,
                "exception_type": (
                    type(exc).__name__
                ),
            },
        )

        raise AppError(
            status_code=503,
            code="MODEL_UNAVAILABLE",
            message=(
                "The local LLM service is unavailable."
            ),
            request_id=request_id,
        ) from exc

    except Exception as exc:

        logger.exception(
            "rag_request_failed",
            extra={
                "request_id": request_id,
                "exception_type": (
                    type(exc).__name__
                ),
            },
        )

        raise AppError(
            status_code=500,
            code="INTERNAL_ERROR",
            message=(
                "The RAG request could not "
                "be completed."
            ),
            request_id=request_id,
        ) from exc


    generated = result.answer
    verified = result.verified_answer


    # =====================================================
    # Citations
    # =====================================================

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


    # =====================================================
    # Claims
    # =====================================================

    claims = [
        ClaimResponse(
            text=claim.text,
            citations=claim.citations,
        )
        for claim in verified.claims.claims
    ]


    # =====================================================
    # Citation verification
    # =====================================================

    citation_verifications = [
        CitationVerificationResponse(
            claim_text=item.claim_text,
            reference=item.reference,
            verdict=item.verdict.value,
            explanation=item.explanation,
        )
        for item
        in verified.citation_verification.verifications
    ]


    # =====================================================
    # Citation metrics
    # =====================================================

    metrics = verified.citation_metrics

    citation_metrics = CitationMetricsResponse(
        citation_precision=(
            metrics.citation_precision
        ),
        citation_coverage=(
            metrics.citation_coverage
        ),
        total_verifications=(
            metrics.total_verifications
        ),
        supported_verifications=(
            metrics.supported_verifications
        ),
        partially_supported_verifications=(
            metrics.partially_supported_verifications
        ),
        unsupported_verifications=(
            metrics.unsupported_verifications
        ),
        contradicted_verifications=(
            metrics.contradicted_verifications
        ),
    )


    # =====================================================
    # Faithfulness
    # =====================================================

    faithfulness = verified.faithfulness

    faithfulness_response = FaithfulnessResponse(
        total_claims=(
            faithfulness.total_claims
        ),
        supported_claims=(
            faithfulness.supported_claims
        ),
        partially_supported_claims=(
            faithfulness.partially_supported_claims
        ),
        unsupported_claims=(
            faithfulness.unsupported_claims
        ),
        contradicted_claims=(
            faithfulness.contradicted_claims
        ),
        claims=[
            FaithfulnessClaimResponse(
                claim_text=item.claim_text,
                verdict=item.verdict.value,
                explanation=item.explanation,
            )
            for item
            in faithfulness.claim_results
        ],
    )


    # =====================================================
    # Abstention
    # =====================================================

    abstention_response = AbstentionResponse(
        should_abstain=(
            verified.abstention.should_abstain
        ),
        decision=(
            verified.abstention.decision.value
        ),
        reasons=(
            verified.abstention.reasons
        ),
    )


    # =====================================================
    # Optional retrieval trace
    # =====================================================

    trace = None

    if request_body.include_trace:

        candidate_responses = []

        for candidate in result.candidates:

            retrieval = (
                candidate.metadata.get(
                    "retrieval",
                    {},
                )
            )

            sources = retrieval.get(
                "sources",
                {},
            )

            dense = sources.get("dense")
            bm25 = sources.get("bm25")

            candidate_responses.append(
                RetrievalCandidateResponse(
                    chunk_id=(
                        candidate.chunk_id
                    ),
                    source=(
                        candidate.metadata.get(
                            "source"
                        )
                    ),
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

                source=(
                    chunk.metadata.get(
                        "source"
                    )
                ),

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
            for chunk
            in result.reranked_chunks
        ]


        trace = RetrievalTraceResponse(
            candidate_count=(
                result.candidate_count
            ),
            evidence_count=(
                result.evidence_count
            ),
            candidates=(
                candidate_responses
            ),
            final_evidence=(
                reranked_responses
            ),
        )


    logger.info(
    "rag_request_completed",
    extra={
        "request_id": request_id,
        "candidate_count": result.candidate_count,
        "evidence_count": result.evidence_count,
        "abstained": (
            verified.abstention.should_abstain
        ),
        "retrieval_ms": (
            result.retrieval_latency_ms
        ),
        "reranking_ms": (
            result.reranking_latency_ms
        ),
        "generation_ms": (
            result.generation_latency_ms
        ),
        "verification_ms": (
            result.verification_latency_ms
        ),
        "total_latency_ms": (
            result.total_latency_ms
        ),
    },
)
    # =====================================================
    # API response
    # =====================================================

    return AskResponse(
        request_id=request_id,
        question=request_body.question,
        answer=verified.final_answer,

        abstained=(
            verified
            .abstention
            .should_abstain
        ),

        citations=citations,

        verification=VerificationResponse(
            claims=claims,

            citation_verification=(
                citation_verifications
            ),

            citation_metrics=(
                citation_metrics
            ),

            faithfulness=(
                faithfulness_response
            ),

            abstention=(
                abstention_response
            ),
        ),

        latency=LatencyResponse(
            retrieval_ms=(
                result.retrieval_latency_ms
            ),
            reranking_ms=(
                result.reranking_latency_ms
            ),
            generation_ms=(
                result.generation_latency_ms
            ),
            verification_ms=(
                result.verification_latency_ms
            ),
            total_ms=(
                result.total_latency_ms
            ),
        ),

        token_usage=TokenUsageResponse(
            input_tokens=(
                generated.input_tokens
            ),
            output_tokens=(
                generated.output_tokens
            ),
            total_tokens=(
                generated.total_tokens
            ),
        ),

        trace=trace,
    )