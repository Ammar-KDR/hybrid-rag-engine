from pathlib import Path

from rag.ingestion.loader import load_document
from rag.chunking.structure_chunking import MarkdownStructureChunker
from rag.chunking.semantic_chunking import SemanticChunker


DATA_PATH = Path("data/raw")


def build_chunks():

    chunker = MarkdownStructureChunker(
        max_chunk_chars=2000,
        overlap=200,
    )

    all_chunks = []


    for file_path in DATA_PATH.glob("*.md"):

        documents = load_document(
            str(file_path)
        )

        for document in documents:

            chunks = chunker.chunk(
                document
            )

            all_chunks.extend(chunks)


    return all_chunks

def build_semantic_chunks():

    chunker = SemanticChunker(
        similarity_threshold=0.55,
        max_chunk_chars=2000,
        min_chunk_chars=300
    )

    all_chunks = []

    for file_path in DATA_PATH.glob("*.md"):

        documents = load_document(
            str(file_path)
        )

        for document in documents:

            chunks = chunker.chunk(
                document
            )

            all_chunks.extend(
                chunks
            )

    return all_chunks