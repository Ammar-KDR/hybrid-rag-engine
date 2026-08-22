from rag.ingestion.model import Chunk


def test_same_chunk_generates_same_id():

    chunk1 = Chunk(
        text="Kubernetes pods run containers",
        source="k8s.md",
        file_type="md",
        chunk_index=0,
        chunking_strategy="semantic",
    )

    chunk2 = Chunk(
        text="Kubernetes pods run containers",
        source="k8s.md",
        file_type="md",
        chunk_index=0,
        chunking_strategy="semantic",
    )

    assert chunk1.chunk_id == chunk2.chunk_id



def test_changed_text_generates_new_id():

    chunk1 = Chunk(
        text="Kubernetes pods run containers",
        source="k8s.md",
        file_type="md",
        chunk_index=0,
        chunking_strategy="semantic",
    )

    chunk2 = Chunk(
        text="Kubernetes pods run applications",
        source="k8s.md",
        file_type="md",
        chunk_index=0,
        chunking_strategy="semantic",
    )

    assert chunk1.chunk_id != chunk2.chunk_id



def test_changed_source_generates_new_id():

    chunk1 = Chunk(
        text="Same content",
        source="a.md",
        file_type="md",
        chunk_index=0,
        chunking_strategy="semantic",
    )

    chunk2 = Chunk(
        text="Same content",
        source="b.md",
        file_type="md",
        chunk_index=0,
        chunking_strategy="semantic",
    )

    assert chunk1.chunk_id != chunk2.chunk_id