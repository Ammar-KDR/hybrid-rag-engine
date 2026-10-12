from fastapi.testclient import TestClient


def test_path_traversal_forbidden(client: TestClient):
    # Attempt directory traversal in document_id
    response = client.get("/v1/documents/evil..payload/source")
    assert response.status_code == 403


def test_nonexistent_document_returns_404(client: TestClient):
    response = client.get("/v1/documents/non_existent_doc_id/source")
    assert response.status_code == 404
