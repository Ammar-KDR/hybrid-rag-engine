from fastapi import APIRouter, Depends

from rag.api.dependencies import get_document_registry, get_rag_pipeline
from rag.api.schemas.brief import BriefRequest, BriefResponse
from rag.briefing.service import MultiDocumentBriefingService
from rag.ingestion.registry import DocumentRegistry
from rag.pipeline import RAGPipeline


router = APIRouter()


@router.post(
    "/brief",
    response_model=BriefResponse,
    summary="Generate a structured multi-document executive briefing with grounded findings",
)
def generate_briefing(
    request: BriefRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    registry: DocumentRegistry = Depends(get_document_registry),
) -> BriefResponse:
    service = MultiDocumentBriefingService(
        pipeline=pipeline,
        registry=registry,
    )

    return service.generate_briefing(
        document_ids=request.document_ids,
        focus=request.focus,
        max_findings=request.max_findings,
    )
