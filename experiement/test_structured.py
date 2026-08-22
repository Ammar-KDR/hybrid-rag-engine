from rag.ingestion.model import Document
from rag.chunking.structure_chunking import MarkdownStructureChunker


def test_markdown_heading_structure():
    document = Document(
        text="""# Kubernetes

Kubernetes manages workloads.

## Pods

Pods contain containers.

### Containers

Containers execute applications.

## Services

Services expose workloads.
""",
        source="runbook.md",
        file_type="md",
    )

    chunker = MarkdownStructureChunker(
        max_chunk_chars=500,
        overlap=75,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) == 4

    assert chunks[0].metadata["heading"] == "Kubernetes"
    assert chunks[0].metadata["heading_level"] == 1
    assert chunks[0].metadata["heading_path"] == [
        "Kubernetes"
    ]

    assert chunks[1].metadata["heading"] == "Pods"
    assert chunks[1].metadata["heading_level"] == 2
    assert chunks[1].metadata["heading_path"] == [
        "Kubernetes",
        "Pods",
    ]

    assert chunks[2].metadata["heading"] == "Containers"
    assert chunks[2].metadata["heading_level"] == 3
    assert chunks[2].metadata["heading_path"] == [
        "Kubernetes",
        "Pods",
        "Containers",
    ]

    assert chunks[3].metadata["heading"] == "Services"
    assert chunks[3].metadata["heading_level"] == 2
    assert chunks[3].metadata["heading_path"] == [
        "Kubernetes",
        "Services",
    ]


def test_structure_chunk_includes_heading_text():
    document = Document(
        text="""## Token Errors

The refresh token has been revoked.
""",
        source="runbook.md",
        file_type="md",
    )

    chunker = MarkdownStructureChunker()

    chunks = chunker.chunk(document)

    assert len(chunks) == 1
    assert "## Token Errors" in chunks[0].text
    assert "refresh token" in chunks[0].text


def test_structure_chunk_handles_text_before_first_heading():
    document = Document(
        text="""Introductory documentation.

# Kubernetes

Kubernetes manages workloads.
""",
        source="runbook.md",
        file_type="md",
    )

    chunker = MarkdownStructureChunker()

    chunks = chunker.chunk(document)

    assert len(chunks) == 2

    assert chunks[0].text == "Introductory documentation."
    assert chunks[0].metadata["heading"] is None
    assert chunks[0].metadata["heading_level"] is None
    assert chunks[0].metadata["heading_path"] == []

    assert chunks[1].metadata["heading"] == "Kubernetes"


def test_structure_chunk_handles_document_without_headings():
    document = Document(
        text="This Markdown document has no headings.",
        source="notes.md",
        file_type="md",
    )

    chunker = MarkdownStructureChunker()

    chunks = chunker.chunk(document)

    assert len(chunks) == 1
    assert chunks[0].text == "This Markdown document has no headings."
    assert chunks[0].metadata["heading"] is None
    assert chunks[0].metadata["heading_level"] is None
    assert chunks[0].metadata["heading_path"] == []


def test_structure_chunk_splits_oversized_section():
    document = Document(
        text="""# Kubernetes

Short intro.

## Pods

ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ
""",
        source="runbook.md",
        file_type="md",
    )

    chunker = MarkdownStructureChunker(
        max_chunk_chars=30,
        overlap=5,
    )

    chunks = chunker.chunk(document)

    pod_chunks = [
        chunk
        for chunk in chunks
        if chunk.metadata["heading"] == "Pods"
    ]

    assert len(pod_chunks) > 1

    for chunk in pod_chunks:
        assert len(chunk.text) <= 30
        assert chunk.chunking_strategy == "structure"
        assert chunk.metadata["heading"] == "Pods"
        assert chunk.metadata["heading_level"] == 2
        assert chunk.metadata["heading_path"] == [
            "Kubernetes",
            "Pods",
        ]

    assert [
        chunk.metadata["section_part"]
        for chunk in pod_chunks
    ] == list(range(len(pod_chunks)))


def test_structure_chunk_indexes_are_global():
    document = Document(
        text="""# Kubernetes

Short intro.

## Pods

ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ
""",
        source="runbook.md",
        file_type="md",
    )

    chunker = MarkdownStructureChunker(
        max_chunk_chars=30,
        overlap=5,
    )

    chunks = chunker.chunk(document)

    assert [
        chunk.chunk_index
        for chunk in chunks
    ] == list(range(len(chunks)))