from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.ingestion.model import Chunk


def test_bm25_retrieves_exact_term():

    chunks = [
        Chunk(
            text="Kubernetes deployments can be restarted using kubectl rollout restart",
            source="kubernetes.md",
            file_type="md",
            chunk_index=0,
            chunking_strategy="markdown"
        ),
        Chunk(
            text="CrashLoopBackOff happens when Kubernetes pods repeatedly fail",
            source="kubernetes.md",
            file_type="md",
            chunk_index=1,
            chunking_strategy="markdown"
        ),
        Chunk(
            text="Docker containers package applications",
            source="docker.md",
            file_type="md",
            chunk_index=0,
            chunking_strategy="markdown"
        )
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(
        "What does CrashLoopBackOff mean?",
        top_k=1
    )

    assert len(results) == 1

    assert "CrashLoopBackOff" in results[0].text