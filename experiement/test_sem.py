from pathlib import Path

from rag.ingestion.loader import load_document
from rag.ingestion.model import Document
from rag.chunking.semantic_chunking import SemanticChunker


def test_semantic_chunk_empty_document():
    document = Document(
        text="",
        source="empty.txt",
        file_type="txt",
    )

    chunker = SemanticChunker(
        similarity_threshold=0.55,
        max_chunk_chars=4000,
    )

    assert chunker.chunk(document) == []


def test_semantic_chunk_single_paragraph():
    document = Document(
        text="Kubernetes Pods are the smallest deployable units.",
        source="single.txt",
        file_type="txt",
    )

    chunker = SemanticChunker(
        similarity_threshold=0.55,
        max_chunk_chars=4000,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.text == document.text
    assert chunk.chunk_index == 0
    assert chunk.chunking_strategy == "semantic"
    assert chunk.source == "single.txt"
    assert chunk.file_type == "txt"

    assert chunk.metadata["start_paragraph"] == 0
    assert chunk.metadata["end_paragraph"] == 0
    assert chunk.metadata["similarity_threshold"] == 0.55


def test_semantic_chunk_real_test_document():
    file_path = Path("data/raw/semantic_test.txt")

    documents = load_document(file_path)

    assert len(documents) == 1

    document = documents[0]

    chunker = SemanticChunker(
        similarity_threshold=0.55,
        max_chunk_chars=4000,
    )

    chunks = chunker.chunk(document)

    # Behavioral test:
    # the document contains multiple distinct topics, so V1 should
    # produce multiple semantic regions.
    assert len(chunks) >= 2

    assert [
        chunk.chunk_index
        for chunk in chunks
    ] == list(range(len(chunks)))

    for chunk in chunks:
        assert chunk.text.strip()

        assert chunk.chunking_strategy == "semantic"
        assert chunk.source == str(file_path)
        assert chunk.file_type == "txt"

        assert "start_paragraph" in chunk.metadata
        assert "end_paragraph" in chunk.metadata
        assert "similarity_threshold" in chunk.metadata

        assert (
            chunk.metadata["start_paragraph"]
            <= chunk.metadata["end_paragraph"]
        )

        assert chunk.metadata["similarity_threshold"] == 0.55