from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from rag.ingestion.service import (
    IngestionService,
)

from rag.api.dependencies import (
    get_ingestion_service,
)

from rag.api.schemas.ingest import (
    IngestResponse,
)


router = APIRouter()


@router.post(
    "/ingest",
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
    print(content)
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
            detail=(
                "Document ingestion failed."
            ),
        ) from exc

    return IngestResponse(
        **result
    )