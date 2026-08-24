from rag.ingestion.pipeline import build_chunks
from rag.retrieval.bm25_retrieval import BM25Retriever


def test_bm25_finds_kubernetes_command():

    chunks = build_chunks()

    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(
        query="kubectl rollout restart deployment",
        top_k=3,
    )

    assert len(results) > 0

    retrieved_text = " ".join(
        chunk.text.lower()
        for chunk in results
    )

    assert "kubectl" in retrieved_text
    assert "restart" in retrieved_text



def test_bm25_finds_docker_command():

    chunks = build_chunks()

    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(
        query="docker logs command",
        top_k=3,
    )

    assert len(results) > 0

    retrieved_text = " ".join(
        chunk.text.lower()
        for chunk in results
    )

    assert "docker" in retrieved_text
    assert "logs" in retrieved_text



def test_bm25_finds_network_term():

    chunks = build_chunks()

    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(
        query="DNS resolution problems",
        top_k=3,
    )

    assert len(results) > 0

    retrieved_text = " ".join(
        chunk.text.lower()
        for chunk in results
    )

    assert "dns" in retrieved_text