from rag.vector_store.qdrant import QdrantVectorStore
from rag.embedding.service import EmbeddingService


def test_search_returns_similar_chunk():

    collection = "test_search"

    store = QdrantVectorStore()

    if store.client.collection_exists(collection):
        store.client.delete_collection(collection)

    store.create_collection(
        collection_name=collection
    )

    embedder = EmbeddingService()

    texts = [
        "Kubernetes pods contain containers",
        "Italian restaurants serve pasta"
    ]


    ids = []

    for i, text in enumerate(texts):

        vector = embedder.embed_text(text)

        point_id = store.add_point(
            collection_name=collection,
            chunk_id=f"chunk_{i}",
            vector=vector,
            payload={
                "text": text
            },
        )

        ids.append(point_id)


    query = embedder.embed_text(
        "What runs inside Kubernetes?"
    )


    results = store.search(
        collection_name=collection,
        query_vector=query,
        limit=1,
    )


    assert len(results) == 1

    assert (
        results[0]
        .payload["text"]
        ==
        "Kubernetes pods contain containers"
    )