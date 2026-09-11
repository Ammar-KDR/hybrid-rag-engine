from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from rag.api.app import create_app
from rag.api.dependencies import (
    get_document_registry,
    get_ingestion_service,
    get_rag_pipeline,
)


def ns(**kwargs):
    return SimpleNamespace(**kwargs)


def build_fake_rag_result():

    supported = ns(
        value="SUPPORTED"
    )

    accept = ns(
        value="ACCEPT"
    )

    generated = ns(
        answer=(
            "Use `docker pull nginx`. [1]"
        ),
        citations=[
            ns(
                reference=1,
                chunk_id="chunk-1",
                source="docker.md",
                page_number=None,
                heading_path=[
                    "Docker",
                    "Images",
                ],
            )
        ],
        input_tokens=100,
        output_tokens=20,
        total_tokens=120,
    )

    claims = ns(
        claims=[
            ns(
                text=(
                    "Use docker pull nginx."
                ),
                citations=[1],
            )
        ]
    )

    citation_verification = ns(
        verifications=[
            ns(
                claim_text=(
                    "Use docker pull nginx."
                ),
                reference=1,
                verdict=supported,
                explanation=(
                    "The evidence supports "
                    "the command."
                ),
            )
        ]
    )

    citation_metrics = ns(
        citation_precision=1.0,
        citation_coverage=1.0,
        total_verifications=1,
        supported_verifications=1,
        partially_supported_verifications=0,
        unsupported_verifications=0,
        contradicted_verifications=0,
    )

    faithfulness = ns(
        total_claims=1,
        supported_claims=1,
        partially_supported_claims=0,
        unsupported_claims=0,
        contradicted_claims=0,
        claim_results=[
            ns(
                claim_text=(
                    "Use docker pull nginx."
                ),
                verdict=supported,
                explanation=(
                    "Supported by evidence."
                ),
            )
        ],
    )

    abstention = ns(
        should_abstain=False,
        decision=accept,
        reasons=[],
    )

    verified = ns(
        final_answer=(
            "Use `docker pull nginx`. [1]"
        ),
        claims=claims,
        citation_verification=(
            citation_verification
        ),
        citation_metrics=citation_metrics,
        faithfulness=faithfulness,
        abstention=abstention,
    )

    candidate = ns(
        chunk_id="chunk-1",
        text="docker pull nginx",
        rank=1,
        score=0.032,
        metadata={
            "source": "docker.md",
            "retrieval": {
                "sources": {
                    "dense": {
                        "rank": 1,
                        "score": 0.91,
                    },
                    "bm25": {
                        "rank": 2,
                        "score": 4.5,
                    },
                }
            },
        },
    )

    reranked = ns(
        chunk_id="chunk-1",
        text="docker pull nginx",
        metadata={
            "source": "docker.md",
        },
        retrieval_rank=1,
        retrieval_score=0.032,
        reranker_score=0.97,
        reranked_rank=1,
        final_score=0.034,
        final_rank=1,
    )

    return ns(
        answer=generated,
        verified_answer=verified,

        retrieval_latency_ms=10.0,
        reranking_latency_ms=20.0,
        generation_latency_ms=30.0,
        verification_latency_ms=40.0,
        total_latency_ms=100.0,

        candidate_count=20,
        evidence_count=5,

        candidates=[candidate],
        reranked_chunks=[reranked],
    )


class FakePipeline:

    def run(
        self,
        question: str,
    ):
        return build_fake_rag_result()


class FakeIngestionService:

    def ingest(
        self,
        filename: str,
        content: bytes,
    ):
        return {
            "document_id": "doc-123",
            "filename": filename,
            "file_type": "md",
            "chunk_count": 3,
            "ingested_at": (
                "2026-09-12T00:00:00+00:00"
            ),
            "chunking_strategy": (
                "markdown_structure"
            ),
            "duplicate": False,
        }


class FakeRegistry:

    def list_documents(self):
        return [
            {
                "document_id": "doc-123",
                "filename": "docker.md",
                "file_type": "md",
                "chunk_count": 3,
                "ingested_at": (
                    "2026-09-12T00:00:00+00:00"
                ),
                "chunking_strategy": (
                    "markdown_structure"
                ),
            }
        ]


@pytest.fixture
def app():

    application = create_app(
        lifespan_handler=None
    )

    application.dependency_overrides[
        get_rag_pipeline
    ] = lambda: FakePipeline()

    application.dependency_overrides[
        get_ingestion_service
    ] = lambda: FakeIngestionService()

    application.dependency_overrides[
        get_document_registry
    ] = lambda: FakeRegistry()

    return application


@pytest.fixture
def client(app):
    return TestClient(app)