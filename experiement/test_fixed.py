import pytest

from rag.ingestion.model import Document
from rag.chunking.fixed_size_chunking import FixedChunker


def test_fixed_chunking_with_overlap():
    document = Document(
        text="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        source="test.txt",
        file_type="txt",
    )

    chunker = FixedChunker(
        chunk_size=10,
        overlap=3,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) == 4

    assert chunks[0].text == "ABCDEFGHIJ"
    assert chunks[1].text == "HIJKLMNOPQ"
    assert chunks[2].text == "OPQRSTUVWX"
    assert chunks[3].text == "VWXYZ"

    assert chunks[0].metadata["start_char"] == 0
    assert chunks[0].metadata["end_char"] == 10

    assert chunks[1].metadata["start_char"] == 7
    assert chunks[1].metadata["end_char"] == 17

    assert chunks[2].metadata["start_char"] == 14
    assert chunks[2].metadata["end_char"] == 24

    assert chunks[3].metadata["start_char"] == 21
    assert chunks[3].metadata["end_char"] == 26


def test_fixed_chunk_contract():
    document = Document(
        text="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        source="policy.txt",
        file_type="txt",
    )

    chunker = FixedChunker(
        chunk_size=10,
        overlap=3,
    )

    chunks = chunker.chunk(document)

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3]

    for chunk in chunks:
        assert chunk.chunking_strategy == "fixed"
        assert chunk.source == "policy.txt"
        assert chunk.file_type == "txt"


def test_fixed_chunk_preserves_document_metadata():
    document = Document(
        text="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        source="manual.pdf",
        file_type="pdf",
        metadata={
            "page_number": 4,
            "page_count": 10,
        },
    )

    chunker = FixedChunker(
        chunk_size=10,
        overlap=3,
    )

    chunks = chunker.chunk(document)

    for chunk in chunks:
        assert chunk.metadata["page_number"] == 4
        assert chunk.metadata["page_count"] == 10


def test_fixed_chunk_metadata_is_copied():
    document = Document(
        text="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        source="test.txt",
        file_type="txt",
        metadata={
            "page_number": 1,
        },
    )

    chunker = FixedChunker(
        chunk_size=10,
        overlap=3,
    )

    chunks = chunker.chunk(document)

    chunks[0].metadata["new_value"] = "changed"

    # Modifying Chunk metadata must not mutate the Document
    assert "new_value" not in document.metadata


def test_fixed_chunk_empty_document():
    document = Document(
        text="",
        source="empty.txt",
        file_type="txt",
    )

    chunker = FixedChunker()

    assert chunker.chunk(document) == []


@pytest.mark.parametrize(
    "chunk_size, overlap",
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 101),
    ],
)
def test_invalid_fixed_chunk_configuration(chunk_size, overlap):
    with pytest.raises(ValueError):
        FixedChunker(
            chunk_size=chunk_size,
            overlap=overlap,
        )