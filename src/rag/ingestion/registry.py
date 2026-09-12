# rag/ingestion/registry.py

import json
from dataclasses import asdict, dataclass
from pathlib import Path


import os

@dataclass
class DocumentRecord:
    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    ingested_at: str
    chunking_strategy: str


class DocumentRegistry:
    def __init__(self, path: Path):
        self.path = path

    def _load(self) -> dict:
        if not self.path.exists():
            return {"documents": []}

        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        with temp_path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                indent=2,
            )

            f.flush()
            os.fsync(f.fileno())

        os.replace(
            temp_path,
            self.path,
        )

    def contains(self, document_id: str) -> bool:
        data = self._load()

        return any(
            document["document_id"] == document_id
            for document in data["documents"]
        )

    def get(self, document_id: str) -> dict | None:
        data = self._load()

        for document in data["documents"]:
            if document["document_id"] == document_id:
                return document

        return None

    def add(self, record: DocumentRecord) -> None:
        data = self._load()

        data["documents"].append(
            asdict(record)
        )

        self._save(data)

    def list_documents(self) -> list[dict]:
        return self._load()["documents"]
    def replace_all(
        self,
        records: list[DocumentRecord],) -> None:
        self._save({
            "documents": [
                asdict(record)
                for record in records
            ]
        })

