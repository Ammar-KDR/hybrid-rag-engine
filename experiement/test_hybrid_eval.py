import json
from pathlib import Path


from rag.ingestion.pipeline import build_chunks

from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore

from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.retrieval.fusion import ReciprocalRankFusion

from rag.evaluation.evaluator import RetrievalEvaluator


DATASET_PATH = (
    "data/evaluation/hybrid_retrieval_dataset.json"
)

COLLECTION_NAME = "documents3"


def load_dataset(path):

    with open(
        path,
        encoding="utf-8"
    ) as f:
        return json.load(f)



def evaluate(
    name,
    retriever,
    dataset
):

    evaluator = RetrievalEvaluator(
        retriever=retriever
    )


    results = evaluator.evaluate(
        dataset,
        k=5
    )


    print("\n")
    print("=" * 60)
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



def category_analysis(
    results
):

    categories = {
        "semantic": [],
        "lexical": [],
        "mixed": []
    }


    for item in results["results"]:

        category = item.get(
            "category",
            "unknown"
        )

        if category in categories:

            categories[category].append(
                item
            )


    print("\n")
    print("=" * 60)
    print("CATEGORY ANALYSIS")
    print("=" * 60)


    for category, items in categories.items():

        if not items:
            continue


        hits = sum(
            item["hit"]
            for item in items
        )


        print("\n")
        print(category)

        print(
            f"Questions: {len(items)}"
        )

        print(
            f"Hit Rate: {hits / len(items):.2f}"
        )

        for item in items:

            if not item["hit"]:

                print(
                    "MISS:",
                    item["question"]
                )



def compare_categories(
    dense,
    bm25,
    hybrid,
    dataset
):

    print("\n")
    print("=" * 60)
    print("RETRIEVER COMPARISON")
    print("=" * 60)


    for i, item in enumerate(dataset):

        dense_hit = dense["results"][i]["hit"]

        bm25_hit = bm25["results"][i]["hit"]

        hybrid_hit = hybrid["results"][i]["hit"]


        if hybrid_hit and (
            not dense_hit
            or not bm25_hit
        ):

            print("\nHYBRID WIN")

            print(
                item["category"],
                ":",
                item["question"]
            )

            print(
                "Dense:",
                dense_hit,
                "BM25:",
                bm25_hit,
                "Hybrid:",
                hybrid_hit
            )



def main():

    dataset = load_dataset(
        DATASET_PATH
    )


    # -------------------------
    # Dense Retriever
    # -------------------------

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()


    dense = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name=COLLECTION_NAME
    )


    # -------------------------
    # BM25 Retriever
    # -------------------------

    chunks = build_chunks()

    bm25 = BM25Retriever(
        chunks
    )

    rrf=ReciprocalRankFusion(60)
    # -------------------------
    # Hybrid Retriever
    # -------------------------

    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        fusion=rrf,
        candidate_k=5
    )


    # -------------------------
    # Evaluate
    # -------------------------

    dense_results = evaluate(
        "Dense Retriever",
        dense,
        dataset
    )


    bm25_results = evaluate(
        "BM25 Retriever",
        bm25,
        dataset
    )


    hybrid_results = evaluate(
        "Hybrid Retriever",
        hybrid,
        dataset
    )


    category_analysis(
        hybrid_results
    )


    compare_categories(
        dense_results,
        bm25_results,
        hybrid_results,
        dataset
    )


if __name__ == "__main__":
    main()