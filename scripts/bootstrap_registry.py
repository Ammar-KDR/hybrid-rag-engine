from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rag.ingestion.chunk_store import ChunkStore
from rag.ingestion.hashing import create_document_id
from rag.ingestion.loader import SUPPORTED_EXTENSIONS
from rag.ingestion.registry import (
    DocumentRecord,
    DocumentRegistry,
)
from rag.config import settings


DATA_PATH = settings.DATA_PATH
CHUNK_STORE_PATH = Path(
    "data/indexes/chunks.jsonl"
)
REGISTRY_PATH = Path(
    "data/registry.json"
)


def main() -> None:
    registry = DocumentRegistry(
        REGISTRY_PATH
    )

    chunk_store = ChunkStore(
        CHUNK_STORE_PATH
    )

    chunks = chunk_store.load_all()

    if not chunks:
        raise RuntimeError(
            "Chunk store is missing or empty. "
            "Run 'python scripts/build_index.py' first."
        )

    chunks_by_source = defaultdict(list)

    for chunk in chunks:
        chunks_by_source[
            str(Path(chunk.source))
        ].append(chunk)

    added = 0
    skipped = 0

    for file_path in sorted(
        DATA_PATH.iterdir()
    ):
        if not file_path.is_file():
            continue

        if (
            file_path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        content = file_path.read_bytes()

        document_id = create_document_id(
            content
        )

        if registry.contains(
            document_id
        ):
            skipped += 1
            continue

        source = str(file_path)

        file_chunks = (
            chunks_by_source.get(
                source,
                [],
            )
        )

        if not file_chunks:
            raise RuntimeError(
                f"No persisted chunks found "
                f"for {file_path}. "
                f"Run 'python scripts/build_index.py' "
                f"to rebuild derived state."
            )

        strategies = {
            chunk.chunking_strategy
            for chunk in file_chunks
        }

        chunking_strategy = (
            next(iter(strategies))
            if len(strategies) == 1
            else "mixed"
        )

        registry.add(
            DocumentRecord(
                document_id=document_id,
                filename=file_path.name,
                file_type=(
                    file_path
                    .suffix
                    .lower()
                    .lstrip(".")
                ),
                chunk_count=len(
                    file_chunks
                ),
                ingested_at=(
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                chunking_strategy=(
                    chunking_strategy
                ),
            )
        )

        added += 1

    print(
        f"Registry bootstrap complete. "
        f"Added: {added}, "
        f"skipped: {skipped}."
    )


if __name__ == "__main__":
    main()