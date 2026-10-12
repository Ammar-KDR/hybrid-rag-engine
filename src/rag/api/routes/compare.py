from fastapi import APIRouter, Depends, HTTPException

from rag.api.dependencies import get_document_registry, get_rag_pipeline
from rag.api.schemas.compare import CompareRequest, CompareResponse
from rag.comparison.service import DocumentComparisonService
from rag.ingestion.registry import DocumentRegistry
from rag.pipeline import RAGPipeline


router = APIRouter()


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare two documents on a topic to detect agreements, version differences, or conflicts",
)
def compare_documents(
    request: CompareRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    registry: DocumentRegistry = Depends(get_document_registry),
) -> CompareResponse:
    service = DocumentComparisonService(
        pipeline=pipeline,
        registry=registry,
    )

    return service.compare(
        document_a_id=request.document_a_id,
        document_b_id_val=request.document_b_id,
        topic=request.topic,
    )
