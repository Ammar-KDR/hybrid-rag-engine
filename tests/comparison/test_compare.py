import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from rag.api.schemas.compare import ComparisonRelationship
from rag.comparison.service import DocumentComparisonService
from rag.retrieval.model import RetrievedChunk


def _dummy_retrieved(chunk_id: str, text: str, doc_id: str, fname: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        metadata={"document_id": doc_id, "filename": fname, "source": f"data/raw/{fname}"},
        score=0.9,
        rank=1,
    )


def test_compare_insufficient_evidence():
    mock_pipeline = MagicMock()
    # Retrieval returns empty for one document
    mock_pipeline.retriever.retrieve.return_value = []
    mock_pipeline.reranker.rerank.return_value = []

    mock_reg = MagicMock()
    mock_reg.get.side_effect = lambda doc_id: {"document_id": doc_id, "filename": f"{doc_id}.md"}

    service = DocumentComparisonService(
        pipeline=mock_pipeline,
        registry=mock_reg,
    )

    res = service.compare("doc_a", "doc_b", "refund period")
    assert res.relationship == ComparisonRelationship.INSUFFICIENT_EVIDENCE
    assert "Insufficient evidence" in res.summary


def test_compare_successful_llm_parse():
    mock_pipeline = MagicMock()
    chunk_a = _dummy_retrieved("ca", "Policy A allows 30 days refund.", "doc_a", "policy_a.md")
    chunk_b = _dummy_retrieved("cb", "Policy B allows 14 days refund effective 2026.", "doc_b", "policy_b.md")

    mock_pipeline.retriever.retrieve.side_effect = [[chunk_a], [chunk_b]]
    mock_pipeline.reranker.rerank.side_effect = [[chunk_a], [chunk_b]]

    mock_reg = MagicMock()
    mock_reg.get.side_effect = lambda doc_id: {"document_id": doc_id, "filename": f"{doc_id}.md"}

    service = DocumentComparisonService(
        pipeline=mock_pipeline,
        registry=mock_reg,
    )

    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    inner_payload = """{
      "relationship": "scope_or_version_difference",
      "summary": "Policy B updates refund window to 14 days starting in 2026.",
      "doc_a_claim": "Allows 30 days refund.",
      "doc_a_scope": "Standard 2025 policy",
      "doc_b_claim": "Allows 14 days refund.",
      "doc_b_scope": "Effective 2026 onwards",
      "resolution_notes": "Apply Policy B for 2026 transactions.",
      "confidence": "high"
    }"""
    mock_resp.read.return_value = json.dumps({
        "choices": [{"message": {"content": inner_payload}}]
    }).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = service.compare("doc_a", "doc_b", "refund window")
        assert res.relationship == ComparisonRelationship.SCOPE_OR_VERSION_DIFFERENCE
        assert len(res.document_a.evidence) == 1
        assert res.document_a.evidence[0].document_id == "doc_a"
        assert len(res.document_b.evidence) == 1
        assert res.document_b.evidence[0].document_id == "doc_b"


def test_compare_endpoint(client: TestClient):
    # Route testing with mocked pipeline
    response = client.post(
        "/v1/compare",
        json={
            "document_a_id": "doc-123",
            "document_b_id": "doc-456",
            "topic": "docker networking",
            "verification_mode": "fast",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "relationship" in data
    assert "document_a" in data
    assert "document_b" in data
