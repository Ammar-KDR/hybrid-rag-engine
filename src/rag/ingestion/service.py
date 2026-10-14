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
        service_router=None,
    ):
        self.data_path = data_path
        self.registry = registry
        self.chunk_store = chunk_store
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.semantic_chunker = semantic_chunker
        self.hybrid_retriever = hybrid_retriever
        self.service_router = service_router


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

            for chunk in new_chunks:
                chunk.metadata["document_id"] = document_id
                chunk.metadata["filename"] = safe_filename
                chunk.metadata["file_type"] = chunk.file_type
                chunk.metadata["source"] = chunk.source

            self._register_document_as_service(document_id, safe_filename, new_chunks)


            # -------------------------------------
            # 6. Prepare embeddings first
            #
            # Batched encoding is significantly faster
            # than encoding one-by-one.
            # -------------------------------------

            chunk_texts = [chunk.text for chunk in new_chunks]
            batch_size = 64
            all_vectors = []
            for i in range(0, len(chunk_texts), batch_size):
                batch_slice = chunk_texts[i : i + batch_size]
                if hasattr(self.embedding_service, "embed_texts"):
                    batch_vectors = self.embedding_service.embed_texts(batch_slice)
                else:
                    batch_vectors = [
                        self.embedding_service.embed_text(t) for t in batch_slice
                    ]
                all_vectors.extend(batch_vectors)

            vectors = list(zip(new_chunks, all_vectors))


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

            qdrant_items = [
                (
                    chunk.chunk_id,
                    vector,
                    {
                        "text": chunk.text,
                        "source": chunk.source,
                        "document_id": document_id,
                        **chunk.metadata,
                    },
                )
                for chunk, vector in vectors
            ]

            if hasattr(self.vector_store, "add_points"):
                self.vector_store.add_points(
                    collection_name=self.collection_name,
                    items=qdrant_items,
                )
            else:
                for chunk, vector in vectors:
                    payload = {
                        "text": chunk.text,
                        "source": chunk.source,
                        "document_id": document_id,
                        **chunk.metadata,
                    }
                    self.vector_store.add_point(
                        collection_name=self.collection_name,
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

    def _register_document_as_service(
        self,
        document_id: str,
        safe_filename: str,
        chunks: list,
    ) -> None:
        """Extracts and registers a ServiceRecord for dynamically ingested documents."""
        import hashlib
        import json
        from rag.config import settings
        from rag.ingestion.service_manifest import ServiceRecord

        # Extract service name from chunk metadata or filename
        service_name = None
        for chunk in chunks:
            s_name = chunk.metadata.get("service_name")
            if s_name and s_name.strip():
                service_name = s_name.strip()
                break

        if not service_name:
            stem = Path(safe_filename).stem
            service_name = stem.replace("_", " ").replace("-", " ")

        service_id = hashlib.sha256(f"{document_id}_{service_name}".encode("utf-8")).hexdigest()[:16]

        # Tag chunks
        for chunk in chunks:
            chunk.metadata["service_id"] = service_id
            chunk.metadata["service_name"] = service_name

        # Build raw sections from chunks
        sections = []
        for i, chunk in enumerate(chunks):
            heading = chunk.metadata.get("heading") or f"قسم {i+1}"
            text = chunk.text
            sec_type = "other"
            if any(w in heading for w in ["شروط", "أهلية"]):
                sec_type = "eligibility"
            elif any(w in heading for w in ["وثائق", "مستندات", "أوراق"]):
                sec_type = "requirements"
            elif any(w in heading for w in ["رسوم", "مالية", "مبالغ"]):
                sec_type = "fees"
            elif any(w in heading for w in ["إجراءات", "خطوات", "تقديم"]):
                sec_type = "steps"
            elif any(w in heading for w in ["ملاحظات", "استثناء"]):
                sec_type = "exceptions"

            sections.append({
                "section_id": f"{service_id}_sec_{i+1}",
                "service_id": service_id,
                "section_type": sec_type,
                "heading": heading,
                "original_text": text,
                "normalized_search_text": text,
                "source_span": {
                    "document_id": document_id,
                    "filename": safe_filename,
                    "page_number": 1,
                    "section_title": heading,
                    "extraction_method": "auto_ingest",
                },
                "order": i + 1,
            })

        # Generate sensible aliases
        aliases = [service_name]
        cleaned = service_name
        for prefix in ["دليل خدمة", "دليل", "خدمة", "معاملة"]:
            cleaned = cleaned.replace(prefix, "").strip()
        if cleaned and cleaned != service_name:
            aliases.append(cleaned)
        stem = Path(safe_filename).stem.replace("_", " ").replace("-", " ")
        if stem not in aliases:
            aliases.append(stem)

        service_record = ServiceRecord(
            service_id=service_id,
            document_id=document_id,
            service_name=service_name,
            aliases=aliases,
            raw_sections=sections,
            review_status="auto_ingested",
        )

        # Update manifest file if it exists
        manifest_path = getattr(settings, "SERVICES_MANIFEST_PATH", Path("data/services_manifest.json"))
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                existing_idx = next(
                    (idx for idx, s in enumerate(manifest_data.get("services", []))
                     if s.get("service_id") == service_id or s.get("document_id") == document_id),
                    None,
                )
                svc_dict = {
                    "service_id": service_id,
                    "document_id": document_id,
                    "service_name": service_name,
                    "aliases": aliases,
                    "organization": None,
                    "start_page": 1,
                    "end_page": 1,
                    "raw_sections": sections,
                    "extraction_warnings": [],
                    "review_status": "auto_ingested",
                }
                if existing_idx is not None:
                    manifest_data["services"][existing_idx] = svc_dict
                else:
                    manifest_data.setdefault("services", []).append(svc_dict)

                manifest_data["services_count"] = len(manifest_data["services"])

                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        # If live service router is available, register service dynamically
        if getattr(self, "service_router", None) is not None:
            self.service_router.register_service(service_record)