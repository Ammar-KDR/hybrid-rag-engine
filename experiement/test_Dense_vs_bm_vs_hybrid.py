from rag.ingestion.pipeline import build_chunks

from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.retrieval.fusion import ReciprocalRankFusion

from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore

from rag.evaluation.evaluator import RetrievalEvaluator
from rag.evaluation.dataset import load_evaluation_dataset


DATASET_PATH = "data/evaluation/retrieval_dataset.json"

COLLECTION_NAME = "documents"


def evaluate_retriever(name, retriever, dataset):

    evaluator = RetrievalEvaluator(
        retriever=retriever
    )

    results = evaluator.evaluate(
        dataset,
        k=5
    )

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print(
        f"Hit Rate@5: {results['hit_rate']:.2f}"
    )

    print(
        f"Recall@5: {results['recall_rate']:.2f}"
    )

    print(
        f"Precision@5: {results['avg_precision']:.2f}"
    )

    print(
        f"MRR@5: {results['mrr_score']:.2f}"
    )

    return results


def analyze_categories(
    dense_results,
    bm25_results,
    hybrid_results
):

    categories = {
        "dense_only": [],
        "bm25_only": [],
        "hybrid_only": [],
        "all": [],
        "neither": []
    }


    for dense_item, bm25_item, hybrid_item in zip(
        dense_results["results"],
        bm25_results["results"],
        hybrid_results["results"]
    ):

        question = dense_item["question"]

        dense_hit = dense_item["hit"]
        bm25_hit = bm25_item["hit"]
        hybrid_hit = hybrid_item["hit"]


        if hybrid_hit:
            categories["hybrid_only"].append(
                question
            )

        if dense_hit and bm25_hit and hybrid_hit:
            categories["all"].append(
                question
            )

        if (
            not dense_hit
            and not bm25_hit
            and not hybrid_hit
        ):
            categories["neither"].append(
                question
            )


    print("\n")
    print("=" * 60)
    print("CATEGORY ANALYSIS")
    print("=" * 60)

    for key, value in categories.items():

        print("\n")
        print(key)

        for item in value:
            print("-", item)


def main():

    dataset = load_evaluation_dataset(
        DATASET_PATH
    )


    # -------------------------
    # Dense Retriever
    # -------------------------

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()


    dense_retriever = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name=COLLECTION_NAME,
    )


    # -------------------------
    # BM25 Retriever
    # -------------------------

    chunks = build_chunks()

    bm25_retriever = BM25Retriever(
        chunks
    )


    # -------------------------
    # Hybrid Retriever
    # -------------------------

    fusion = ReciprocalRankFusion(
        k=60
    )


    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        fusion=fusion,
        candidate_k=5
    )


    # -------------------------
    # Evaluation
    # -------------------------

    dense_results = evaluate_retriever(
        "Dense Retriever",
        dense_retriever,
        dataset
    )


    bm25_results = evaluate_retriever(
        "BM25 Retriever",
        bm25_retriever,
        dataset
    )


    hybrid_results = evaluate_retriever(
        "Hybrid Retriever",
        hybrid_retriever,
        dataset
    )


    analyze_categories(
        dense_results,
        bm25_results,
        hybrid_results
    )


if __name__ == "__main__":
    main()