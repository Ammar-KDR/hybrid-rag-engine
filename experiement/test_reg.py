from rag.ingestion.registry import (
    DocumentRecord,
    DocumentRegistry,
)


def make_record(
    document_id: str,
    filename: str,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        filename=filename,
        file_type="md",
        chunk_count=2,
        ingested_at="2026-09-12T00:00:00+00:00",
        chunking_strategy="structure",
    )


def test_replace_all_removes_stale_records(
    tmp_path,
):
    registry = DocumentRegistry(
        tmp_path / "registry.json"
    )

    registry.add(
        make_record(
            "old-document",
            "old.md",
        )
    )

    registry.replace_all([
        make_record(
            "current-document",
            "current.md",
        )
    ])

    documents = registry.list_documents()

    assert len(documents) == 1
    assert (
        documents[0]["document_id"]
        == "current-document"
    )