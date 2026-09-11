from rag.api.dependencies import (
    get_ingestion_service,
)


def test_ingest_success(client):

    response = client.post(
        "/v1/ingest",
        files={
            "file": (
                "docker.md",
                b"# Docker\nSome content",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["filename"]
        == "docker.md"
    )

    assert (
        data["document_id"]
        == "doc-123"
    )

    assert (
        data["duplicate"]
        is False
    )

    assert (
        data["chunk_count"]
        == 3
    )


def test_ingest_duplicate(app):

    class DuplicateService:

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
                "duplicate": True,
            }

    app.dependency_overrides[
        get_ingestion_service
    ] = lambda: DuplicateService()

    from fastapi.testclient import (
        TestClient,
    )

    client = TestClient(app)

    response = client.post(
        "/v1/ingest",
        files={
            "file": (
                "docker.md",
                b"same bytes",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["duplicate"]
        is True
    )


def test_unsupported_file_returns_400(
    app,
):

    class RejectingService:

        def ingest(
            self,
            filename: str,
            content: bytes,
        ):
            raise ValueError(
                "Unsupported file extension."
            )

    app.dependency_overrides[
        get_ingestion_service
    ] = lambda: RejectingService()

    from fastapi.testclient import (
        TestClient,
    )

    client = TestClient(app)

    response = client.post(
        "/v1/ingest",
        files={
            "file": (
                "virus.exe",
                b"bad",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400