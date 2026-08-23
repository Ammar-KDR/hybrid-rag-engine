from pathlib import Path

from rag.ingestion.loader import load_document
from rag.chunking.structure_chunking import MarkdownStructureChunker
from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore


DATA_PATH = Path("data/raw")
COLLECTION_NAME = "documents"


def build_index():

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()

    vector_store.create_collection(
        collection_name=COLLECTION_NAME,
        vector_size=384,
    )

    chunker = MarkdownStructureChunker(
        max_chunk_chars=2000,
        overlap=200,
    )


    for file_path in DATA_PATH.glob("*.md"):

        print("\n" + "=" * 60)
        print(f"Processing: {file_path.name}")

        documents = load_document(
            str(file_path)
        )

        for document in documents:

            chunks = chunker.chunk(document)

            print(
                f"Generated {len(chunks)} chunks"
            )

            for chunk in chunks:

                vector = embedding_service.embed_text(
                    chunk.text
                )

                payload = {
                    "text": chunk.text,
                    "source": chunk.source,
                    "file_type": chunk.file_type,
                    "chunk_index": chunk.chunk_index,
                    "chunking_strategy": chunk.chunking_strategy,
                    **chunk.metadata,
                }

                vector_store.add_point(
                    collection_name=COLLECTION_NAME,
                    chunk_id=chunk.chunk_id,
                    vector=vector,
                    payload=payload,
                )

                print(
                    f"Indexed: {chunk.chunk_id}"
                )


if __name__ == "__main__":
    build_index()