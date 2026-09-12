import json
import os
from pathlib import Path
from typing import Any

from .model import Chunk


class ChunkStore:
    def __init__(self, path: Path):
        self.path = path

    def load_all(self) -> list[Chunk]:
        if not self.path.exists():
            return []

        chunks: list[Chunk] = []

        with self.path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid chunk store JSON at line {line_number}."
                    ) from exc

                chunks.append(self._deserialize(data))

        return chunks

    def replace_all(self, chunks: list[Chunk]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            for chunk in chunks:
                record = self._serialize(chunk)
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, self.path)

    def add_many(self, chunks: list[Chunk]) -> None:
        existing_chunks = self.load_all()

        chunks_by_id = {
            chunk.chunk_id: chunk
            for chunk in existing_chunks
        }

        for chunk in chunks:
            chunks_by_id.setdefault(
                chunk.chunk_id,
                chunk,
            )

        self.replace_all(list(chunks_by_id.values()))

    @staticmethod
    def _serialize(chunk: Chunk) -> dict[str, Any]:
        return {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "source": chunk.source,
            "file_type": chunk.file_type,
            "chunk_index": chunk.chunk_index,
            "chunking_strategy": chunk.chunking_strategy,
            "metadata": chunk.metadata,
        }

    @staticmethod
    def _deserialize(data: dict[str, Any]) -> Chunk:
        chunk = Chunk(
            text=data["text"],
            source=data["source"],
            file_type=data["file_type"],
            chunk_index=data["chunk_index"],
            chunking_strategy=data["chunking_strategy"],
            metadata=data.get("metadata", {}),
        )

        stored_chunk_id = data.get("chunk_id")

        if stored_chunk_id is not None and stored_chunk_id != chunk.chunk_id:
            raise ValueError(
                f"Chunk ID mismatch for source '{chunk.source}' "
                f"at chunk index {chunk.chunk_index}."
            )

        return chunk