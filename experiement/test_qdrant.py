from rag.vector_store.qdrant import QdrantVectorStore


def test_qdrant_connection():

    store = QdrantVectorStore()

    collections = store.client.get_collections()

    assert collections is not None