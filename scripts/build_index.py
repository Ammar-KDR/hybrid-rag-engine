from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rag.embedding.service import EmbeddingService
from rag.ingestion.chunk_store import ChunkStore
from rag.ingestion.hashing import create_document_id
from rag.ingestion.loader import SUPPORTED_EXTENSIONS
from rag.ingestion.pipeline import build_chunks
from rag.ingestion.registry import (
    DocumentRecord,
    DocumentRegistry,
)
from rag.vector_store.qdrant import QdrantVectorStore
from rag.chunking.semantic_chunking import SemanticChunker
from rag.config import settings


DATA_PATH = settings.DATA_PATH
CHUNK_STORE_PATH = settings.CHUNK_STORE_PATH
REGISTRY_PATH = settings.REGISTRY_PATH

COLLECTION_NAME = settings.QDRANT_COLLECTION


def main() -> None:
    print("Building index...")

    # -------------------------------------------------
    # 1. Discover canonical source documents
    # -------------------------------------------------

    source_files = sorted(
        file_path
        for file_path in DATA_PATH.iterdir()
        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    )

    if not source_files:
        raise RuntimeError(
            f"No supported documents found in {DATA_PATH}."
        )

    print(
        f"Found {len(source_files)} source documents."
    )

    # -------------------------------------------------
    # 2. Build deterministic document identities
    # -------------------------------------------------

    document_ids: dict[str, str] = {}

    for file_path in source_files:
        document_ids[str(file_path)] = (
            create_document_id(
                file_path.read_bytes()
            )
        )

    # -------------------------------------------------
    # 3. Chunk the canonical corpus ONCE
    # -------------------------------------------------
    embedding_service = EmbeddingService()

    semantic_chunker = SemanticChunker(
        model=embedding_service.model,
        similarity_threshold=0.55,
        max_chunk_chars=2000,
        min_chunk_chars=300,
    )

    chunks = build_chunks(semantic_chunker=semantic_chunker)

    if not chunks:
        raise RuntimeError(
            "Corpus produced no chunks."
        )

    print(
        f"Built {len(chunks)} chunks."
    )

    # -------------------------------------------------
    # 4. Validate every source produced chunks
    # -------------------------------------------------

    chunks_by_source = defaultdict(list)

    for chunk in chunks:
        chunks_by_source[
            str(Path(chunk.source))
        ].append(chunk)

    for file_path in source_files:
        source = str(file_path)

        if not chunks_by_source[source]:
            raise RuntimeError(
                f"Document produced no chunks: "
                f"{file_path}"
            )

    # -------------------------------------------------
    # 5. Prepare embeddings BEFORE destructive writes
    # -------------------------------------------------

    
    vectors = embedding_service.embed_texts(
        [
            chunk.text
            for chunk in chunks
        ]
    )

    if len(vectors) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match "
            "chunk count."
        )

    print(
        f"Embedded {len(vectors)} chunks."
    )

    # -------------------------------------------------
    # 6. Persist canonical derived chunks
    # -------------------------------------------------

    chunk_store = ChunkStore(
        CHUNK_STORE_PATH
    )

    chunk_store.replace_all(
        chunks
    )

    print(
        f"Saved chunk snapshot to "
        f"{CHUNK_STORE_PATH}."
    )

    # -------------------------------------------------
    # 7. Rebuild Qdrant dense index
    # -------------------------------------------------

    vector_store = QdrantVectorStore(url=settings.QDRANT_URL)

    vector_store.reset_collection(
        collection_name=COLLECTION_NAME,
        vector_size=(
            embedding_service.info.dimension
        ),
    )

    for chunk, vector in zip(
        chunks,
        vectors,
    ):
        source = str(
            Path(chunk.source)
        )

        document_id = (
            document_ids[source]
        )

        payload = {
            "text": chunk.text,
            "source": chunk.source,
            "document_id": document_id,
            **chunk.metadata,
        }

        vector_store.add_point(
            collection_name=COLLECTION_NAME,
            chunk_id=chunk.chunk_id,
            vector=vector,
            payload=payload,
        )

    print(
        f"Indexed {len(chunks)} chunks "
        f"into Qdrant."
    )

    # -------------------------------------------------
    # 8. Rebuild registry from canonical corpus
    # -------------------------------------------------

    records: list[DocumentRecord] = []

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    for file_path in source_files:

        source = str(file_path)

        file_chunks = (
            chunks_by_source[source]
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

        records.append(
            DocumentRecord(
                document_id=(
                    document_ids[source]
                ),
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
                ingested_at=timestamp,
                chunking_strategy=(
                    chunking_strategy
                ),
            )
        )

    registry = DocumentRegistry(
        REGISTRY_PATH
    )

    registry.replace_all(
        records
    )

    print(
        f"Registry synchronized with "
        f"{len(records)} documents."
    )

    print("Index build complete.")


if __name__ == "__main__":
    main()