# rag/ingestion/registry.py

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from rag.ingestion.hashing import create_document_id
from rag.ingestion.loader import SUPPORTED_EXTENSIONS
from rag.ingestion.pipeline import build_chunks_for_file
from datetime import datetime, timezone

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

        with self.path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
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

def bootstrap_registry(
    registry: DocumentRegistry,
        data_path: Path,
        ) -> None:

    for file_path in data_path.iterdir():

        if not file_path.is_file():
                continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

        content = file_path.read_bytes()

        document_id = create_document_id(content)

        if registry.contains(document_id):
            continue

        chunks = build_chunks_for_file(file_path)

        if not chunks:
            continue

        strategies = {
                chunk.chunking_strategy
                for chunk in chunks
            }

        chunking_strategy = (
                next(iter(strategies))
                if len(strategies) == 1
                else "mixed"
            )

        record = DocumentRecord(
                document_id=document_id,
                filename=file_path.name,
                file_type=file_path.suffix.lower().lstrip("."),
                chunk_count=len(chunks),
                ingested_at=datetime.now(timezone.utc).isoformat(),
                chunking_strategy=chunking_strategy,
            )

        registry.add(record)