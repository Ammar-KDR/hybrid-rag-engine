from typing import Any

import requests


class RAGAPIClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
    ):
        self.base_url = base_url.rstrip("/")


    def ask(
        self,
        question: str,
        include_trace: bool = False,
    ) -> dict[str, Any]:

        response = requests.post(
            f"{self.base_url}/v1/ask",
            json={
                "question": question,
                "include_trace": include_trace,
            },
            timeout=120,
        )

        self._raise_for_api_error(
            response
        )

        return response.json()


    def ingest(
        self,
        filename: str,
        content: bytes,
    ) -> dict[str, Any]:

        response = requests.post(
            f"{self.base_url}/v1/ingest",
            files={
                "file": (
                    filename,
                    content,
                )
            },
            timeout=120,
        )

        self._raise_for_api_error(
            response
        )

        return response.json()


    def list_documents(
        self,
    ) -> list[dict[str, Any]]:

        response = requests.get(
            f"{self.base_url}/v1/documents",
            timeout=30,
        )

        self._raise_for_api_error(
            response
        )

        return response.json()


    @staticmethod
    def _raise_for_api_error(
        response: requests.Response,
    ) -> None:

        if response.ok:
            return

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return

        error = data.get(
            "error",
            {}
        )

        message = error.get(
            "message"
        )

        request_id = data.get(
            "request_id"
        )

        if not message:
            message = data.get(
                "detail",
                "API request failed."
            )

        if request_id:
            message = (
                f"{message}\n\n"
                f"Request ID: {request_id}"
            )

        raise RuntimeError(
            message
        )