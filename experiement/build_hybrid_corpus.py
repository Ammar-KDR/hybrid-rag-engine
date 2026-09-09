from pathlib import Path
import json

from rag.ingestion.pipeline import build_chunks
from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore


NEW_COLLECTION_NAME = "documents3"

OUTPUT_FILE = Path(
    "data/evaluation/chunks2.json"
)


def create_collection(
    vector_store,
    embedding_dimension
):

    vector_store.create_collection(
        collection_name=NEW_COLLECTION_NAME,
        vector_size=embedding_dimension,
    )


def ingest_chunks(
    chunks,
    embedding_service,
    vector_store
):

    for chunk in chunks:

        vector = embedding_service.embed_text(
            chunk.text
        )


        payload = {
            "text": chunk.text,
            "source": chunk.source,
            **chunk.metadata,
        }


        vector_store.add_point(
            collection_name=NEW_COLLECTION_NAME,
            chunk_id=chunk.chunk_id,
            vector=vector,
            payload=payload,
        )


def export_chunks(
    chunks
):

    exported = []

    for chunk in chunks:

        exported.append(
            {
                "chunk_id": chunk.chunk_id,

                "source": chunk.source,

                "heading": chunk.metadata.get(
                    "heading"
                ),

                "metadata": {
                    "source": chunk.source,
                    "file_type": chunk.file_type,
                    "chunk_index": chunk.chunk_index,
                    "chunking_strategy": chunk.chunking_strategy,
                    **chunk.metadata,
                },

                "text": chunk.text,
            }
        )


    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            exported,
            f,
            indent=4,
            ensure_ascii=False,
        )


    print(
        f"Exported {len(exported)} chunks"
    )

    print(
        f"Saved to {OUTPUT_FILE}"
    )


def main():

    print("=" * 60)
    print("Building Hybrid Retrieval Corpus")
    print("=" * 60)


    # -------------------------
    # Build chunks
    # -------------------------

    chunks = build_chunks()


    print(
        f"Generated {len(chunks)} chunks"
    )


    # -------------------------
    # Embeddings
    # -------------------------

    embedding_service = EmbeddingService()


    test_vector = embedding_service.embed_text(
        "test"
    )


    embedding_dimension = len(
        test_vector
    )


    print(
        f"Embedding dimension: {embedding_dimension}"
    )


    # -------------------------
    # Qdrant
    # -------------------------

    vector_store = QdrantVectorStore()


    print(
        f"Creating collection: {NEW_COLLECTION_NAME}"
    )


    create_collection(
        vector_store,
        embedding_dimension
    )


    # -------------------------
    # Insert vectors
    # -------------------------

    print(
        "Uploading chunks..."
    )


    ingest_chunks(
        chunks,
        embedding_service,
        vector_store
    )


    print(
        "Upload complete"
    )


    # -------------------------
    # Export snapshot
    # -------------------------

    print(
        "Hybrid corpus ready."
    )


if __name__ == "__main__":
    main()