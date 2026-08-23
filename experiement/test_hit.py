from rag.evaluation.dataset import load_evaluation_dataset
from rag.evaluation.evaluator import RetrievalEvaluator

from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore
from rag.retrieval.Dense_retrieval import DenseRetriever


DATASET_PATH = (
    "data/evaluation/retrieval_dataset.json"
)


def main():

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()

    retriever = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name="documents",
    )


    dataset = load_evaluation_dataset(
        DATASET_PATH
    )


    evaluator = RetrievalEvaluator(
        retriever=retriever
    )


    results = evaluator.evaluate(
        dataset,
        k=5,
    )


    print("=" * 60)

    print(
        f"Hit Rate@5: {results['hit_rate']:.2f}"
    )
    print(
        f"Hit recall@5: {results['recall_rate']:.2f}"
        )
    
    print(
        f"Hit precision@5: {results['avg_precision']:.2f}"
        )

    print(
        f"MRR@5: {results['mrr_score']:.2f}"
        )    
    

    print("=" * 60)


    for result in results["results"]:

        print("-" * 60)

        print(
            result["question"]
        )

        print(
            "Hit:",
            result["hit"]
        )
        print(
                    "recall:",
                    result["recall"]
                )
        print(
                    "precision:",
                    result["precision"]
                )
        print(
                    "mrr:",
                    result["mrr"]
                )

        print(
            "Retrieved:",
            result["retrieved_ids"]
        )



if __name__ == "__main__":
    main()