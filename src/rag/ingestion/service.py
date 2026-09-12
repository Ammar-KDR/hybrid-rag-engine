from datetime import datetime, timezone
from pathlib import Path

from rag.ingestion.hashing import create_document_id
from rag.ingestion.loader import SUPPORTED_EXTENSIONS
from rag.ingestion.pipeline import build_chunks_for_file
from rag.ingestion.chunk_store import ChunkStore
from rag.ingestion.registry import (
    DocumentRecord,
    DocumentRegistry,
)
from rag.retrieval.bm25_retrieval import BM25Retriever


class IngestionService:

    def __init__(
        self,
        data_path: Path,
        registry: DocumentRegistry,
        embedding_service,
        semantic_chunker,
        vector_store,
        chunk_store: ChunkStore,
        collection_name: str,
        hybrid_retriever,
    ):
        self.data_path = data_path
        self.registry = registry
        self.chunk_store = chunk_store
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.semantic_chunker = semantic_chunker
        self.hybrid_retriever = hybrid_retriever


    def ingest(
        self,
        filename: str,
        content: bytes,
    ) -> dict:

        # -----------------------------------------
        # 1. Validate filename / extension
        # -----------------------------------------

        safe_filename = Path(filename).name

        extension = (
            Path(safe_filename)
            .suffix
            .lower()
        )

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{extension}'. "
                f"Supported types: "
                f"{sorted(SUPPORTED_EXTENSIONS)}"
            )

        if not content:
            raise ValueError(
                "Uploaded file is empty."
            )


        # -----------------------------------------
        # 2. Deterministic document identity
        # -----------------------------------------

        document_id = create_document_id(
            content
        )


        # -----------------------------------------
        # 3. Exact duplicate check
        # -----------------------------------------

        existing = self.registry.get(
            document_id
        )

        if existing is not None:
            return {
                **existing,
                "duplicate": True,
            }


        # -----------------------------------------
        # 4. Save canonical source document
        #
        # Prefix with document ID so two different
        # files named manual.pdf cannot overwrite
        # each other.
        # -----------------------------------------

        self.data_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = (
            f"{document_id}_{safe_filename}"
        )

        stored_path = (
            self.data_path
            / stored_filename
        )

        stored_path.write_bytes(content)


        try:
            # -------------------------------------
            # 5. Chunk ONLY the new document
            # -------------------------------------
            existing_chunks = []

            old_bm25 = (
                self.hybrid_retriever
                .bm25_retriever
            )

            chunk_store_updated = False
            bm25_updated = False

            new_chunks = build_chunks_for_file(
                stored_path,
                semantic_chunker=self.semantic_chunker
            )

            if not new_chunks:
                raise ValueError(
                    "Document produced no chunks."
                )


            # -------------------------------------
            # 6. Prepare embeddings first
            #
            # Do expensive work before changing
            # Qdrant or live BM25 state.
            # -------------------------------------

            vectors = []

            for chunk in new_chunks:

                vector = (
                    self.embedding_service
                    .embed_text(chunk.text)
                )

                vectors.append(
                    (chunk, vector)
                )


            # -------------------------------------
            # 7. Build prospective BM25
            #
            # build_chunks() now sees all files,
            # including the new canonical file.
            # -------------------------------------

            existing_chunks = (
                self.chunk_store.load_all()
            )

            chunks_by_id = {
                chunk.chunk_id: chunk
                for chunk in existing_chunks
            }

            for chunk in new_chunks:
                chunks_by_id[chunk.chunk_id] = chunk

            all_chunks = list(
                chunks_by_id.values()
            )
            self.chunk_store.replace_all(
                all_chunks
            )

            chunk_store_updated = True

            new_bm25 = BM25Retriever(
                chunks=all_chunks
            )


            # -------------------------------------
            # 8. Upsert ONLY new chunks to Qdrant
            # -------------------------------------

            for chunk, vector in vectors:

                payload = {
                    "text": chunk.text,
                    "source": chunk.source,
                    "document_id": document_id,
                    **chunk.metadata,
                }

                self.vector_store.add_point(
                    collection_name=(
                        self.collection_name
                    ),
                    chunk_id=chunk.chunk_id,
                    vector=vector,
                    payload=payload,
                )


            # -------------------------------------
            # 9. Replace live BM25
            # -------------------------------------

            self.hybrid_retriever.replace_bm25_retriever(
                new_bm25
            )
            bm25_updated = True


            # -------------------------------------
            # 10. Registry LAST
            #
            # A registry record means ingestion
            # completed successfully.
            # -------------------------------------

            strategies = {
                chunk.chunking_strategy
                for chunk in new_chunks
            }

            chunking_strategy = (
                next(iter(strategies))
                if len(strategies) == 1
                else "mixed"
            )

            record = DocumentRecord(
                document_id=document_id,
                filename=safe_filename,
                file_type=(
                    extension.lstrip(".")
                ),
                chunk_count=len(new_chunks),
                ingested_at=(
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                chunking_strategy=(
                    chunking_strategy
                ),
            )

            self.registry.add(record)

            return {
                **record.__dict__,
                "duplicate": False,
            }

        except Exception:

            if bm25_updated:
                self.hybrid_retriever.replace_bm25_retriever(
                    old_bm25
                )

            if chunk_store_updated:
                self.chunk_store.replace_all(
                    existing_chunks
                )

            if not self.registry.contains(
                document_id
            ):
                stored_path.unlink(
                    missing_ok=True
                )

            raise