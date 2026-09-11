from openai import APIConnectionError
import httpx

from rag.api.dependencies import (
    get_rag_pipeline,
)


def test_ask_success(client):

    response = client.post(
        "/v1/ask",
        json={
            "question": (
                "How do I pull "
                "a Docker image?"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_id"]
    assert data["abstained"] is False

    assert (
        data["answer"]
        == "Use `docker pull nginx`. [1]"
    )

    assert len(
        data["citations"]
    ) == 1

    assert (
        data["latency"]["total_ms"]
        == 100.0
    )

    assert data["trace"] is None


def test_ask_with_trace(client):

    response = client.post(
        "/v1/ask",
        json={
            "question": (
                "How do I pull "
                "a Docker image?"
            ),
            "include_trace": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["trace"] is not None

    assert (
        data["trace"]["candidate_count"]
        == 20
    )

    assert (
        data["trace"]["candidates"][0]
        ["dense"]["rank"]
        == 1
    )

    assert (
        data["trace"]["candidates"][0]
        ["bm25"]["rank"]
        == 2
    )


def test_empty_question_returns_422(
    client,
):

    response = client.post(
        "/v1/ask",
        json={
            "question": "     ",
        },
    )

    assert response.status_code == 422


def test_model_unavailable_returns_503(
    app,
):

    class BrokenPipeline:

        def run(
            self,
            question: str,
        ):
            request = httpx.Request(
                "POST",
                "http://localhost:1234/v1/chat/completions",
            )

            raise APIConnectionError(
                request=request
            )

    app.dependency_overrides[
        get_rag_pipeline
    ] = lambda: BrokenPipeline()

    from fastapi.testclient import (
        TestClient,
    )

    client = TestClient(app)

    response = client.post(
        "/v1/ask",
        json={
            "question": "Hello",
        },
    )

    assert response.status_code == 503

    data = response.json()

    assert (
        data["error"]["code"]
        == "MODEL_UNAVAILABLE"
    )

    assert data["request_id"]