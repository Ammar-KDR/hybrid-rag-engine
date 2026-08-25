import json


from rag.ingestion.pipeline import build_chunks

from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore

from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.retrieval.fusion import ReciprocalRankFusion



DATASET_PATH = (
    "data/evaluation/hybrid_retrieval_dataset.json"
)

COLLECTION_NAME = "documents3"



def load_dataset():

    with open(
        DATASET_PATH,
        encoding="utf-8"
    ) as f:

        return json.load(f)



def print_results(
    name,
    results,
    expected_ids
):

    print("\n")
    print("-" * 60)
    print(name)
    print("-" * 60)


    for r in results:

        marker = (
            "✅"
            if r.chunk_id in expected_ids
            else " "
        )

        print(
            marker,
            "Rank:",
            r.rank,
            "Score:",
            r.score
        )

        print(
            "Chunk:",
            r.chunk_id
        )

        print(
            r.text[:300]
            .replace("\n", " ")
        )

        print()



def main():

    dataset = load_dataset()


    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()


    dense = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name=COLLECTION_NAME
    )


    chunks = build_chunks()

    bm25 = BM25Retriever(
        chunks
    )


    fusion = ReciprocalRankFusion(
        k=60
    )


    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        fusion=fusion
    )



    for item in dataset:

        question = item["question"]

        expected_ids = set(
            item["expected_chunk_ids"]
        )


        hybrid_results = hybrid.retrieve(
            question,
            top_k=5
        )


        hybrid_ids = {
            r.chunk_id
            for r in hybrid_results
        }


        if not expected_ids.intersection(
            hybrid_ids
        ):

            print("\n")
            print("=" * 80)
            print(
                "FAILED QUERY"
            )
            print("=" * 80)

            print(
                "Category:",
                item.get("category")
            )

            print(
                "Question:",
                question
            )

            print(
                "\nExpected:"
            )

            for eid in expected_ids:
                print(eid)



            dense_results = dense.retrieve(
                question,
                top_k=5
            )

            bm25_results = bm25.retrieve(
                question,
                top_k=5
            )


            print_results(
                "DENSE",
                dense_results,
                expected_ids
            )


            print_results(
                "BM25",
                bm25_results,
                expected_ids
            )


            print_results(
                "HYBRID",
                hybrid_results,
                expected_ids
            )



if __name__ == "__main__":
    main()