from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from rag.briefing.service import MultiDocumentBriefingService
from rag.retrieval.model import RetrievedChunk


def _dummy_retrieved(chunk_id: str, text: str, doc_id: str, fname: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        metadata={"document_id": doc_id, "filename": fname, "source": f"data/raw/{fname}"},
        score=0.88,
        rank=1,
    )


def test_briefing_service_empty():
    mock_pipeline = MagicMock()
    mock_pipeline.retriever.retrieve.return_value = []
    mock_pipeline.reranker.rerank.return_value = []

    mock_reg = MagicMock()
    mock_reg.get.return_value = {"filename": "empty.md"}

    service = MultiDocumentBriefingService(
        pipeline=mock_pipeline,
        registry=mock_reg,
    )

    res = service.generate_briefing(["doc-1"], focus="test")
    assert res.findings == []
    assert "No relevant evidence" in res.executive_summary


def test_briefing_endpoint(client: TestClient):
    response = client.post(
        "/v1/brief",
        json={
            "document_ids": ["doc-123"],
            "focus": "Security compliance and container defaults",
            "max_findings": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert "findings" in data
    assert data["document_count"] == 1
