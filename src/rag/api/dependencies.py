from fastapi import Request

from rag.pipeline import RAGPipeline
from rag.ingestion.registry import DocumentRegistry
from rag.ingestion.service import IngestionService


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