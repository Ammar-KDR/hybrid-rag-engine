from datetime import datetime, timezone
from pathlib import Path

from rag.ingestion.hashing import create_document_id
from rag.ingestion.loader import SUPPORTED_EXTENSIONS
from rag.ingestion.pipeline import (
    build_chunks,
    build_chunks_for_file,
)
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
        vector_store,
        collection_name: str,
        hybrid_retriever,
    ):
        self.data_path = data_path
        self.registry = registry

        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.collection_name = collection_name

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

            new_chunks = build_chunks_for_file(
                stored_path
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

            all_chunks = build_chunks()

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
            # If we failed before successful
            # ingestion, don't leave the uploaded
            # source file behind.
            #
            # NOTE:
            # A Qdrant failure partway through its
            # loop could still have written some
            # deterministic points. Retrying is
            # safe because their UUIDs are stable.

            if not self.registry.contains(
                document_id
            ):
                stored_path.unlink(
                    missing_ok=True
                )

            raise