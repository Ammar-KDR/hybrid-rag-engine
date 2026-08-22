from rag.vector_store.qdrant import QdrantVectorStore
from rag.embedding.service import EmbeddingService


def run_experiment():

    collection = "dense_retrieval_demo"

    store = QdrantVectorStore()

    if store.client.collection_exists(collection):
        store.client.delete_collection(collection)

    store.create_collection(
        collection_name=collection
    )

    embedder = EmbeddingService()


    documents = [
        {
            "text": """
            Kubernetes Pods are the smallest deployable units
            in Kubernetes. A Pod contains one or more containers
            that share networking and storage.
            """,
            "source": "kubernetes.md",
            "topic": "containers",
        },

        {
            "text": """
            To restart a Kubernetes deployment, use:
            kubectl rollout restart deployment <name>
            This creates new Pods with the updated configuration.
            """,
            "source": "kubernetes.md",
            "topic": "deployment",
        },

        {
            "text": """
            Database backups should be performed regularly.
            Backups protect against data loss and allow recovery
            after failures.
            """,
            "source": "database.md",
            "topic": "backup",
        },

        {
            "text": """
            Network troubleshooting includes checking latency,
            packet loss, connectivity, and service availability.
            """,
            "source": "network.md",
            "topic": "network",
        },
    ]


    # Insert documents

    for index, doc in enumerate(documents):

        vector = embedder.embed_text(
            doc["text"]
        )

        store.add_point(
            collection_name=collection,
            chunk_id=f"chunk_{index}",
            vector=vector,
            payload=doc,
        )


    queries = [
        "How can I recover a failed Kubernetes workload?",
        "What command restarts a deployment?",
        "How do I avoid losing database data?",
    ]


    for query in queries:

        print("\n========================")
        print("QUERY:")
        print(query)

        query_vector = embedder.embed_text(
            query
        )

        results = store.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=3,
        )


        print("\nRESULTS:")

        for result in results:

            print("----------------")
            print(
                "score:",
                result.score
            )

            print(
                "source:",
                result.payload["source"]
            )

            print(
                "topic:",
                result.payload["topic"]
            )

            print(
                result.payload["text"][:150]
            )


if __name__ == "__main__":
    run_experiment()