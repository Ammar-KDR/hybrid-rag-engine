from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.ingestion.model import Chunk
from rag.retrieval.model import RetrievedChunk


def test_bm25_returns_retrieved_chunk():

    chunks = [
        Chunk(
            text="Kubernetes CrashLoopBackOff troubleshooting",
            source="kubernetes.md",
            file_type="md",
            chunk_index=0,
            chunking_strategy="markdown"
        )
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(
        "CrashLoopBackOff",
        top_k=1
    )

    result = results[0]

    assert isinstance(result, RetrievedChunk)

    assert result.chunk_id is not None
    assert result.text is not None
    assert result.metadata is not None
    assert result.score is not None
    assert result.rank == 1