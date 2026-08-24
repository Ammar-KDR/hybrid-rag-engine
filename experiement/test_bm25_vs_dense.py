from rag.ingestion.pipeline import build_chunks

from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.Dense_retrieval import DenseRetriever

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
    categories = {
    "dense_only": [],
    "bm25_only": [],
    "both": [],
    "neither": []
}


    for dense_item, bm25_item in zip(
        dense_results["results"],
        bm25_results["results"]
    ):

        dense_hit = dense_item["hit"]
        bm25_hit = bm25_item["hit"]

        if dense_hit and not bm25_hit:
            categories["dense_only"].append(
                dense_item["question"]
            )

        elif bm25_hit and not dense_hit:
            categories["bm25_only"].append(
                dense_item["question"]
            )

        elif dense_hit and bm25_hit:
            categories["both"].append(
                dense_item["question"]
            )

        else:
            categories["neither"].append(
                dense_item["question"]
            )
    for k,v in categories.items():
        print("=" * 60)
        print(f"{k}\n\n{v}")



if __name__ == "__main__":
    main()