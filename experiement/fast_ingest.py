from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from pydantic import BaseModel, field_validator

from rag.factory import create_rag_pipeline
from rag.pipeline import RAGPipeline
from rag.ingestion.registry import bootstrap_registry
from rag.ingestion.hashing import create_document_id
from rag.ingestion.loader import SUPPORTED_EXTENSIONS
from rag.ingestion.registry import DocumentRegistry
from rag.ingestion.service import IngestionService
import uuid
from fastapi.responses import JSONResponse
import logging


# =========================================================
# Application lifecycle
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing RAG pipeline...")

    app.state.rag_pipeline = create_rag_pipeline()
    pipeline = app.state.rag_pipeline

    hybrid_retriever = pipeline.retriever
    dense_retriever = (
        hybrid_retriever.dense_retriever
    )

    registry = DocumentRegistry(
        Path("data/registry.json")
    )
    bootstrap_registry(
    registry=registry,
    data_path=Path("data/raw"),
    )

    app.state.document_registry = registry

    app.state.document_registry = DocumentRegistry(
        Path("data/registry.json")
    )
    app.state.ingestion_service = (
    IngestionService(
        data_path=Path("data/raw"),

        registry=registry,

        embedding_service=(
            dense_retriever
            .embedding_service
        ),

        vector_store=(
            dense_retriever
            .vector_store
        ),

        collection_name=(
            dense_retriever
            .collection_name
        ),

        hybrid_retriever=(
            hybrid_retriever
        ),
    )
)
    print("Application ready.")

    yield

    print("Application shutting down.")


app = FastAPI(
    title="Hybrid RAG API",
    version="1.0.0",
    lifespan=lifespan,
)



# =========================================================
# Dependencies
# =========================================================

def get_rag_pipeline(
    request: Request,
) -> RAGPipeline:
    return request.app.state.rag_pipeline

def get_ingestion_service(
    request: Request,
) -> IngestionService:

    return request.app.state.ingestion_service

def get_document_registry(
    request: Request,
) -> DocumentRegistry:
    return request.app.state.document_registry


# =========================================================
# /v1/ask request model
# =========================================================

class AskRequest(BaseModel):
    question: str
    include_trace: bool = False

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


# =========================================================
# Citation models
# =========================================================

class CitationResponse(BaseModel):
    reference: int
    chunk_id: str
    source: str

    page_number: Optional[int] = None
    heading_path: list[str]


# =========================================================
# Latency + token usage
# =========================================================

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


# =========================================================
# Verification models
# =========================================================

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


# =========================================================
# Retrieval trace models
# =========================================================

class RankingStageResponse(BaseModel):
    rank: Optional[int] = None
    score: Optional[float] = None


class RetrievalCandidateResponse(BaseModel):
    chunk_id: str
    source: Optional[str] = None
    text: str

    rrf: RankingStageResponse

    dense: Optional[
        RankingStageResponse
    ] = None

    bm25: Optional[
        RankingStageResponse
    ] = None


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

    candidates: list[
        RetrievalCandidateResponse
    ]

    final_evidence: list[
        RerankedChunkResponse
    ]

# =========================================================
# ingestion
# =========================================================
class IngestResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    ingested_at: str
    chunking_strategy: str
    duplicate: bool

# =========================================================
# Main /ask response
# =========================================================

class AskResponse(BaseModel):
    request_id:str
    question: str
    answer: str
    abstained: bool

    citations: list[CitationResponse]

    verification: VerificationResponse

    latency: LatencyResponse
    token_usage: TokenUsageResponse

    trace: Optional[
        RetrievalTraceResponse
    ] = None

# =========================================================
# errors
# =========================================================

class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    request_id: str
    error: ErrorDetail

class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        request_id: str,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id


logger = logging.getLogger(
    "rag.api"
)
logging.basicConfig(
    level=logging.INFO,
)
# =========================================================
# POST /v1/ask
# =========================================================

@app.post(
    "/v1/ask",
    response_model=AskResponse,
)
def ask(
    request_body: AskRequest,
    pipeline: RAGPipeline = Depends(
        get_rag_pipeline
    ),
):
    # -----------------------------------------------------
    # Run existing Day 1-10 pipeline
    # -----------------------------------------------------
 
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

    except Exception as exc:
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


    # -----------------------------------------------------
    # Citations
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Claims
    # -----------------------------------------------------

    claims = [
        ClaimResponse(
            text=claim.text,
            citations=claim.citations,
        )
        for claim in verified.claims.claims
    ]


    # -----------------------------------------------------
    # Citation verification
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Citation metrics
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Faithfulness
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Abstention
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Optional retrieval trace
    # -----------------------------------------------------

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
                            rank=dense.get(
                                "rank"
                            ),
                            score=dense.get(
                                "score"
                            ),
                        )
                        if dense
                        else None
                    ),

                    bm25=(
                        RankingStageResponse(
                            rank=bm25.get(
                                "rank"
                            ),
                            score=bm25.get(
                                "score"
                            ),
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

                retrieval=(
                    RankingStageResponse(
                        rank=(
                            chunk.retrieval_rank
                        ),
                        score=(
                            chunk.retrieval_score
                        ),
                    )
                ),

                reranker=(
                    RankingStageResponse(
                        rank=(
                            chunk.reranked_rank
                        ),
                        score=(
                            chunk.reranker_score
                        ),
                    )
                ),

                final=(
                    RankingStageResponse(
                        rank=(
                            chunk.final_rank
                        ),
                        score=(
                            chunk.final_score
                        ),
                    )
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


    # -----------------------------------------------------
    # Final API response
    # -----------------------------------------------------

    return AskResponse(
        request_id=request_id,
        question=request_body.question,

        # Final VERIFIED answer,
        # not pre-verification generation
        answer=verified.final_answer,

        abstained=(
            verified.abstention.should_abstain
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



# =========================================================
# POST /v1/ingest
#
# IMPORTANT:
# This is ONLY the first safe ingestion stage.
#
# It currently:
#   - accepts a file
#   - validates extension
#   - hashes file bytes
#   - checks registry
#
# It does NOT yet:
#   - save the file
#   - chunk it
#   - embed it
#   - update Qdrant
#   - rebuild BM25
#   - write registry record
# =========================================================

@app.post(
    "/v1/ingest",
    response_model=IngestResponse,
)
async def ingest(
    file: UploadFile = File(...),

    ingestion_service: IngestionService = Depends(
        get_ingestion_service
    ),
):
    filename = file.filename or ""

    content = await file.read()

    try:
        result = ingestion_service.ingest(
            filename=filename,
            content=content,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed.",
        ) from exc

    return IngestResponse(
        **result
    )

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    ingested_at: str
    chunking_strategy: str

@app.get(
    "/v1/documents",
    response_model=list[DocumentResponse],
)
def list_documents(
    registry: DocumentRegistry = Depends(
        get_document_registry
    ),
):
    return [
        DocumentResponse(**document)
        for document in registry.list_documents()
    ]


@app.exception_handler(AppError)
async def app_error_handler(
    request: Request,
    exc: AppError,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "request_id": exc.request_id,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )