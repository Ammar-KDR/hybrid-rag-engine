def test_list_documents(client):

    response = client.get(
        "/v1/documents"
    )

    assert response.status_code == 200

    documents = response.json()

    assert len(documents) == 1

    assert (
        documents[0]["filename"]
        == "docker.md"
    )

    assert (
        documents[0]["chunk_count"]
        == 3
    )