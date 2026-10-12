from typing import Any, Optional
import requests


class RAGAPIClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
    ):
        self.base_url = base_url.rstrip("/")

    def get_health(self) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/v1/health",
            timeout=10,
        )
        self._raise_for_api_error(response)
        return response.json()

    def ask(
        self,
        question: str,
        history: Optional[list[dict[str, str]]] = None,
        document_ids: Optional[list[str]] = None,
        include_trace: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "question": question,
            "include_trace": include_trace,
        }
        if history:
            payload["history"] = history
        if document_ids:
            payload["document_ids"] = document_ids

        response = requests.post(
            f"{self.base_url}/v1/ask",
            json=payload,
            timeout=120,
        )
        self._raise_for_api_error(response)
        return response.json()

    def compare(
        self,
        document_a_id: str,
        document_b_id: str,
        topic: str,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/v1/compare",
            json={
                "document_a_id": document_a_id,
                "document_b_id": document_b_id,
                "topic": topic,
                "verification_mode": "fast",
            },
            timeout=120,
        )
        self._raise_for_api_error(response)
        return response.json()

    def brief(
        self,
        document_ids: list[str],
        focus: str = "Executive Summary, Critical Policies, and Key Dates",
        max_findings: int = 8,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/v1/brief",
            json={
                "document_ids": document_ids,
                "focus": focus,
                "max_findings": max_findings,
                "verification_mode": "fast",
            },
            timeout=180,
        )
        self._raise_for_api_error(response)
        return response.json()

    def get_page_preview(self, document_id: str, page_number: int) -> Optional[bytes]:
        try:
            response = requests.get(
                f"{self.base_url}/v1/documents/{document_id}/pages/{page_number}/preview",
                timeout=15,
            )
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None

    def get_document_source(self, document_id: str) -> bytes:
        response = requests.get(
            f"{self.base_url}/v1/documents/{document_id}/source",
            timeout=30,
        )
        self._raise_for_api_error(response)
        return response.content

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
        self._raise_for_api_error(response)
        return response.json()

    def list_documents(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.base_url}/v1/documents",
            timeout=30,
        )
        self._raise_for_api_error(response)
        return response.json()

    @staticmethod
    def _raise_for_api_error(response: requests.Response) -> None:
        if response.ok:
            return

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return

        error = data.get("error", {})
        message = error.get("message")
        request_id = data.get("request_id")

        if not message:
            message = data.get("detail", "API request failed.")

        if request_id:
            message = f"{message}\n\nRequest ID: {request_id}"

        raise RuntimeError(message)