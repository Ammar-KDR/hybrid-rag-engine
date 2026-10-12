import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse

from rag.api.dependencies import get_document_registry
from rag.config import settings
from rag.ingestion.registry import DocumentRegistry

try:
    import pymupdf  # PyMuPDF
except ImportError:
    pymupdf = None


router = APIRouter()


def _resolve_document_path(document_id: str, registry: DocumentRegistry) -> Path:
    # 1. Anti-traversal check on input id
    if ".." in document_id or "/" in document_id or "\\" in document_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Path traversal attempt detected.",
        )

    record = registry.get(document_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{document_id}' not found in registry.",
        )

    filename = record.get("filename", "")
    safe_data_root = settings.DATA_PATH.resolve()

    # Check candidate paths: prefixed first, then direct filename
    candidates = [
        settings.DATA_PATH / f"{document_id}_{filename}",
        settings.DATA_PATH / filename,
    ]

    target_path = None
    for cand in candidates:
        if cand.exists():
            target_path = cand.resolve()
            break

    if target_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Source file for document '{document_id}' not found on disk.",
        )

    # Strict containment check
    try:
        target_path.relative_to(safe_data_root)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Path resolves outside safe data repository.",
        )

    return target_path


@router.get(
    "/documents/{document_id}/source",
    summary="Safely stream canonical document source file",
)
def get_document_source(
    document_id: str,
    registry: DocumentRegistry = Depends(get_document_registry),
):
    target_path = _resolve_document_path(document_id, registry)
    return FileResponse(
        path=str(target_path),
        filename=target_path.name,
        media_type="application/octet-stream",
    )


@router.get(
    "/documents/{document_id}/pages/{page_number}/preview",
    summary="Render PDF page preview image",
)
def get_page_preview(
    document_id: str,
    page_number: int,
    registry: DocumentRegistry = Depends(get_document_registry),
):
    target_path = _resolve_document_path(document_id, registry)

    if target_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Page preview only supported for PDF files, found '{target_path.suffix}'.",
        )

    if pymupdf is None:
        raise HTTPException(
            status_code=500,
            detail="PyMuPDF library is not available for PDF rendering.",
        )

    try:
        doc = pymupdf.open(str(target_path))
        # 1-indexed to 0-indexed conversion
        zero_indexed = page_number - 1 if page_number >= 1 else page_number
        if zero_indexed < 0 or zero_indexed >= len(doc):
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_number} out of range (document has {len(doc)} pages).",
            )

        page = doc.load_page(zero_indexed)
        # 150 DPI provides high crisp readability
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        return Response(content=img_bytes, media_type="image/png")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to render PDF page: {exc}",
        )
