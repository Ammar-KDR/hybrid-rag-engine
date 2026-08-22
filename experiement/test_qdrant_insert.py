from rag.vector_store.qdrant import QdrantVectorStore
from rag.embedding.service import EmbeddingService


def test_insert_vector():

    collection = "test_insert"

    store = QdrantVectorStore()

    if store.client.collection_exists(collection):
        store.client.delete_collection(collection)

    store.create_collection(
        collection_name=collection
    )

    embedder = EmbeddingService()

    text = "Kubernetes pods contain containers"

    vector = embedder.embed_text(text)

    point_id=store.add_point(
        collection_name=collection,
        chunk_id="test123",
        vector=vector,
        payload={
            "text": text,
            "source": "test.md",
        },
    )

    result = store.client.retrieve(
    collection_name=collection,
    ids=[point_id],
    )   

    assert len(result) == 1
    assert result[0].payload["text"] == text