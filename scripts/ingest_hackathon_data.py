import argparse
import shutil
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rag.chunking.semantic_chunking import SemanticChunker
from rag.config import settings
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


def ingest_and_index(source_folder: Path | None = None) -> None:
    start_time = time.perf_counter()
    data_path = settings.DATA_PATH
    data_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(" [42 Irbid AI Hackathon] Fast Ingestion & Indexing Pipeline")
    print("=" * 60)


    # 1. If an external folder is provided, copy supported documents into data/raw
    if source_folder and source_folder.resolve() != data_path.resolve():
        print(f"\n[1/5] Importing files from external folder: {source_folder}")
        if not source_folder.exists():
            raise FileNotFoundError(f"Source folder does not exist: {source_folder}")

        imported_count = 0
        for item in source_folder.rglob("*"):
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                target_dest = data_path / item.name
                # Avoid collision if filename already exists
                if target_dest.exists() and target_dest.read_bytes() != item.read_bytes():
                    doc_hash = create_document_id(item.read_bytes())[:8]
                    target_dest = data_path / f"{doc_hash}_{item.name}"
                shutil.copy2(item, target_dest)
                imported_count += 1
                print(f"  + Imported: {item.name}")
        print(f"Total imported files: {imported_count}")
    else:
        print(f"\n[1/5] Scanning internal data folder: {data_path}")

    # 2. Discover supported documents recursively
    source_files = sorted(
        file_path
        for file_path in data_path.rglob("*")
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not source_files:
        raise RuntimeError(
            f"No supported documents found in {data_path}. "
            f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    print(f"Found {len(source_files)} supported documents for indexing.")

    # 3. Create document identities
    document_ids: dict[str, str] = {}
    for file_path in source_files:
        document_ids[str(file_path)] = create_document_id(file_path.read_bytes())

    # 4. Chunk corpus
    print("\n[2/5] Chunking documents...")
    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL_NAME)
    semantic_chunker = SemanticChunker(
        model=embedding_service.model,
        similarity_threshold=0.55,
        max_chunk_chars=2000,
        min_chunk_chars=300,
    )

    chunks = build_chunks(semantic_chunker=semantic_chunker, data_path=data_path)
    if not chunks:
        raise RuntimeError("Corpus produced no chunks.")

    print(f"Generated {len(chunks)} chunks.")

    # Group chunks by source
    chunks_by_source = defaultdict(list)
    for chunk in chunks:
        chunks_by_source[str(Path(chunk.source))].append(chunk)

    # 5. Embed chunks
    print("\n[3/5] Generating dense embeddings...")
    vectors = embedding_service.embed_texts([chunk.text for chunk in chunks])
    print(f"Successfully embedded {len(vectors)} vectors.")

    # 6. Save chunk store
    print("\n[4/5] Saving chunk store & indexing vector store...")
    settings.CHUNK_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    chunk_store = ChunkStore(settings.CHUNK_STORE_PATH)
    chunk_store.replace_all(chunks)

    # Vector store setup (local embedded or remote Docker)
    if settings.QDRANT_STORAGE_MODE == "local":
        print(f"Using local embedded Qdrant at: {settings.QDRANT_LOCAL_PATH}")
        vector_store = QdrantVectorStore(path=settings.QDRANT_LOCAL_PATH)
    else:
        print(f"Connecting to Qdrant server at: {settings.QDRANT_URL}")
        vector_store = QdrantVectorStore(url=settings.QDRANT_URL)

    vector_store.reset_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vector_size=embedding_service.info.dimension,
    )

    for chunk, vector in zip(chunks, vectors):
        source = str(Path(chunk.source))
        doc_id = document_ids[source]
        payload = {
            "text": chunk.text,
            "source": chunk.source,
            "document_id": doc_id,
            **chunk.metadata,
        }
        vector_store.add_point(
            collection_name=settings.QDRANT_COLLECTION,
            chunk_id=chunk.chunk_id,
            vector=vector,
            payload=payload,
        )

    # 7. Update document registry
    print("\n[5/5] Updating document registry...")
    records: list[DocumentRecord] = []
    timestamp = datetime.now(timezone.utc).isoformat()

    for file_path in source_files:
        source = str(file_path)
        file_chunks = chunks_by_source[source]
        strategies = {chunk.chunking_strategy for chunk in file_chunks}
        chunking_strategy = (
            next(iter(strategies)) if len(strategies) == 1 else "mixed"
        )
        records.append(
            DocumentRecord(
                document_id=document_ids[source],
                filename=file_path.name,
                file_type=file_path.suffix.lower().lstrip("."),
                chunk_count=len(file_chunks),
                ingested_at=timestamp,
                chunking_strategy=chunking_strategy,
            )
        )

    settings.REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry = DocumentRegistry(settings.REGISTRY_PATH)
    registry.replace_all(records)

    elapsed = time.perf_counter() - start_time
    print("=" * 60)
    print(f" [OK] Indexing complete in {elapsed:.2f} seconds!")
    print(f" Total documents: {len(records)}")
    print(f" Total chunks:    {len(chunks)}")
    print(f" Storage mode:    {settings.QDRANT_STORAGE_MODE}")
    print("=" * 60)



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fast 1-Command Document Ingestion & Indexing for Hackathons"
    )
    parser.add_argument(
        "--path",
        "--folder",
        type=Path,
        default=None,
        help="Path to folder containing documents to ingest and index",
    )
    args = parser.parse_args()
    ingest_and_index(args.path)


if __name__ == "__main__":
    main()
