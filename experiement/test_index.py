from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.ingestion.model import Chunk


def test_bm25_index_creation():

    chunks = [
        Chunk(
            text="Kubernetes deployment restart command",
            source="kubernetes.md",
            file_type="md",
            chunk_index=0,
            chunking_strategy="markdown"
        ),
        Chunk(
            text="Docker containers run applications",
            source="docker.md",
            file_type="md",
            chunk_index=0,
            chunking_strategy="markdown"
        ),
        Chunk(
            text="CrashLoopBackOff happens when Kubernetes pods fail",
            source="kubernetes.md",
            file_type="md",
            chunk_index=1,
            chunking_strategy="markdown"
        )
    ]

    retriever = BM25Retriever(chunks)


    assert retriever.index is not None
    assert retriever.chunks == chunks