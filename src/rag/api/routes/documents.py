from fastapi import (
    APIRouter,
    Depends,
)

from rag.ingestion.registry import (
    DocumentRegistry,
)

from rag.api.dependencies import (
    get_document_registry,
)

from rag.api.schemas.documents import (
    DocumentResponse,
)


router = APIRouter()


@router.get(
    "/documents",
    response_model=list[DocumentResponse],
)
def list_documents(
    registry: DocumentRegistry = Depends(
        get_document_registry
    ),
):
    return [
        DocumentResponse(
            **document
        )
        for document
        in registry.list_documents()
    ]