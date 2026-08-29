from sentence_transformers import CrossEncoder

from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore

from rag.reranking.reranker import CrossEncoderReranker


# --------------------------------------------------
# Configuration
# --------------------------------------------------

COLLECTION_NAME = "documents3"

QUERY = "How do I restart a Kubernetes deployment?"

CANDIDATE_K = 20
FINAL_K = 5


# --------------------------------------------------
# Printing helpers
# --------------------------------------------------

def print_dense_candidates(candidates):

    print("\n" + "=" * 80)
    print(f"DENSE TOP {CANDIDATE_K} — BEFORE RERANKING")
    print("=" * 80)

    for candidate in candidates:

        print("\n" + "-" * 80)

        print(
            f"Retrieval rank: {candidate.rank}"
        )

        print(
            f"Retrieval score: {candidate.score:.4f}"
        )

        print(
            f"Chunk ID: {candidate.chunk_id}"
        )

        print(
            f"Source: {candidate.metadata.get('source')}"
        )

        print(
            f"Topic: {candidate.metadata.get('topic')}"
        )

        print("\nText:")

        print(
            candidate.text[:400]
        )


def print_reranked_results(results):

    print("\n\n" + "=" * 80)
    print(f"RERANKED TOP {FINAL_K}")
    print("=" * 80)

    for result in results:

        print("\n" + "-" * 80)
        print(result)

        print(
            f"Reranked rank: {result.reranked_rank}"
        )

        print(
            f"Original retrieval rank: {result.retrieval_rank}"
        )

        print(
            f"Original retrieval score: "
            f"{result.retrieval_score:.4f}"
        )

        print(
            f"Reranker score: "
            f"{result.reranker_score:.4f}"
        )

        print(
            f"Chunk ID: {result.chunk_id}"
        )

        print(
            f"Source: {result.metadata.get('source')}"
        )

        print(
            f"Topic: {result.metadata.get('topic')}"
        )

        print("\nText:")

        print(
            result.text[:400]
        )


# --------------------------------------------------
# Main experiment
# --------------------------------------------------

def main():

    # ----------------------------------------------
    # Dense Retriever
    # ----------------------------------------------

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()

    dense_retriever = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name=COLLECTION_NAME,
    )


    # ----------------------------------------------
    # Cross-Encoder Reranker
    # ----------------------------------------------

    cross_encoder = CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L6-v2"
    )

    reranker = CrossEncoderReranker(
        cross_encoder
    )


    # ----------------------------------------------
    # Stage 1 — Dense candidate retrieval
    # ----------------------------------------------

    candidates = dense_retriever.retrieve(
        query=QUERY,
        top_k=CANDIDATE_K,
    )

    print_dense_candidates(
        candidates
    )


    # ----------------------------------------------
    # Stage 2 — Cross-encoder reranking
    # ----------------------------------------------

    reranked_results = reranker.rerank(
        query=QUERY,
        candidates=candidates,
        top_k=FINAL_K,
    )

    print_reranked_results(
        reranked_results
    )


if __name__ == "__main__":
    main()