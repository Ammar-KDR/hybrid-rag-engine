from sentence_transformers import CrossEncoder

from rag.retrieval.model import RetrievedChunk
from rag.reranking.reranker import CrossEncoderReranker


def test_real_cross_encoder_ranks_relevant_chunk_first():
    model = CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L6-v2"
    )

    reranker = CrossEncoderReranker(model)

    candidates = [
        RetrievedChunk(
            chunk_id="storage",
            text=(
                "PersistentVolumes provide persistent storage "
                "for Kubernetes workloads."
            ),
            metadata={"source": "kubernetes.md"},
            score=0.90,
            rank=1,
        ),
        RetrievedChunk(
            chunk_id="restart",
            text=(
                "Restart a Kubernetes deployment using "
                "kubectl rollout restart deployment <name>."
            ),
            metadata={"source": "kubernetes.md"},
            score=0.70,
            rank=2,
        ),
        RetrievedChunk(
            chunk_id="pods",
            text=(
                "Pods are the smallest deployable units "
                "in Kubernetes."
            ),
            metadata={"source": "kubernetes.md"},
            score=0.60,
            rank=3,
        ),
    ]

    results = reranker.rerank(
        query="How do I restart a Kubernetes deployment?",
        candidates=candidates,
        top_k=3,
    )

    print("\nRERANKED RESULTS")
    print("=" * 60)

    for result in results:
        print(
            f"reranked_rank={result.reranked_rank} | "
            f"chunk_id={result.chunk_id} | "
            f"reranker_score={result.reranker_score:.4f} | "
            f"retrieval_rank={result.retrieval_rank} | "
            f"retrieval_score={result.retrieval_score}"
        )

    assert len(results) == 3

    assert results[0].chunk_id == "restart"

    assert results[0].reranked_rank == 1

    assert results[0].retrieval_rank == 2

    assert results[0].retrieval_score == 0.70

    assert (
        results[0].reranker_score
        > results[1].reranker_score
    )

    assert (
        results[1].reranker_score
        > results[2].reranker_score
    )


def test_real_cross_encoder_respects_top_k():
    model = CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L6-v2"
    )

    reranker = CrossEncoderReranker(model)

    candidates = [
        RetrievedChunk(
            chunk_id="storage",
            text=(
                "PersistentVolumes provide persistent storage "
                "for Kubernetes workloads."
            ),
            metadata={},
            score=0.90,
            rank=1,
        ),
        RetrievedChunk(
            chunk_id="restart",
            text=(
                "Restart a Kubernetes deployment using "
                "kubectl rollout restart deployment <name>."
            ),
            metadata={},
            score=0.70,
            rank=2,
        ),
        RetrievedChunk(
            chunk_id="pods",
            text=(
                "Pods are the smallest deployable units "
                "in Kubernetes."
            ),
            metadata={},
            score=0.60,
            rank=3,
        ),
    ]

    results = reranker.rerank(
        query="How do I restart a Kubernetes deployment?",
        candidates=candidates,
        top_k=1,
    )

    assert len(results) == 1

    assert results[0].chunk_id == "restart"

    assert results[0].reranked_rank == 1