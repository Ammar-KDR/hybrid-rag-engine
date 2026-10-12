from fastapi.testclient import TestClient


def test_health_endpoint_schema(client: TestClient):
    response = client.get("/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ("ready", "degraded")
    assert data["offline_mode"] is True

    # Check component dictionaries
    assert "ollama" in data
    assert "ready" in data["ollama"]
    assert "model" in data["ollama"]

    assert "qdrant" in data
    assert "ready" in data["qdrant"]

    assert "embedding_model" in data
    assert data["embedding_model"]["ready"] is True

    assert "reranker" in data
    assert data["reranker"]["ready"] is True

    assert "document_count" in data
    assert isinstance(data["document_count"], int)
    assert "chunk_count" in data
    assert isinstance(data["chunk_count"], int)
