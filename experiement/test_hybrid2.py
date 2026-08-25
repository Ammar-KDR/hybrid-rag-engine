from pathlib import Path

from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.retrieval.fusion import ReciprocalRankFusion

from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore

from rag.ingestion.pipeline import build_chunks 
from rag.chunking.structure_chunking import MarkdownStructureChunker 


def load_evaluation_chunks():
    """
    Load the same evaluation chunks used previously.
    Adjust this function depending on your existing loading pipeline.
    """

    chunks = build_chunks()

    return chunks


def print_results(query, results):

    print("=" * 80)
    print("QUERY:")
    print(query)

    print()

    for result in results:

        print("-" * 80)

        print(
            f"Rank: {result.rank}"
        )

        print(
            f"Chunk ID: {result.chunk_id}"
        )

        print(
            f"Score: {result.score}"
        )

        print(
            f"Source: {result.metadata.get('source')}"
        )

        retrieval = result.metadata.get(
            "retrieval",
            {}
        )

        print(
            "Retrieval:"
        )

        print(retrieval)

        print()

        print(
            result.text[:300]
        )


def main():

    # Load chunks for BM25
    chunks = load_evaluation_chunks()


    # Dense retrieval dependencies

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()


    dense = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name="documents"
    )


    bm25 = BM25Retriever(
        chunks
    )


    fusion = ReciprocalRankFusion(
        k=60
    )


    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        fusion=fusion,
        candidate_k=5
    )


    queries = [
        "How can I recover a failed Kubernetes workload?",
        "What does CrashLoopBackOff mean?",
        "How do Docker containers store persistent data?"
    ]


    for query in queries:

        results = hybrid.retrieve(
            query=query,
            top_k=5
        )

        print_results(
            query,
            results
        )


if __name__ == "__main__":
    main()