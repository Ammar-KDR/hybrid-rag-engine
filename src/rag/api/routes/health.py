import urllib.request
from fastapi import APIRouter, Depends

from rag.api.dependencies import (
    get_document_registry,
    get_rag_pipeline,
)
from rag.api.schemas.health import (
    ComponentStatus,
    HealthResponse,
)
from rag.config import settings
from rag.ingestion.registry import DocumentRegistry
from rag.pipeline import RAGPipeline


router = APIRouter()


def _check_ollama() -> bool:
    try:
        base_url = settings.OLLAMA_BASE_URL.replace("/v1", "").rstrip("/")
        url = f"{base_url}/api/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "RAG-HealthCheck"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def _check_qdrant(pipeline: RAGPipeline) -> bool:
    try:
        client = pipeline.retriever.dense_retriever.vector_store.client
        client.get_collection(collection_name=settings.QDRANT_COLLECTION)
        return True
    except Exception:
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
)
def get_health(
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    registry: DocumentRegistry = Depends(get_document_registry),
) -> HealthResponse:
    ollama_ready = _check_ollama()
    qdrant_ready = _check_qdrant(pipeline)

    doc_count = len(registry.list_documents())
    retriever = getattr(pipeline, "retriever", None)
    bm25 = getattr(retriever, "bm25_retriever", None)
    chunk_count = len(getattr(bm25, "chunks", []))

    all_ready = ollama_ready and qdrant_ready

    return HealthResponse(
        status="ready" if all_ready else "degraded",
        offline_mode=True,
        ollama=ComponentStatus(
            ready=ollama_ready,
            model=settings.OLLAMA_MODEL,
        ),
        qdrant=ComponentStatus(
            ready=qdrant_ready,
            mode=settings.QDRANT_STORAGE_MODE,
        ),
        embedding_model=ComponentStatus(
            ready=True,
            name=settings.EMBEDDING_MODEL_NAME.split("/")[-1],
        ),
        reranker=ComponentStatus(
            ready=True,
            name=settings.RERANKER_MODEL_NAME.split("/")[-1],
        ),
        document_count=doc_count,
        chunk_count=chunk_count,
    )
