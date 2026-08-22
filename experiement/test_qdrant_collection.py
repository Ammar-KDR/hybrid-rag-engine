from rag.vector_store.qdrant import QdrantVectorStore


def test_create_collection():

    store = QdrantVectorStore()

    collection_name = "test_documents"

    if store.client.collection_exists(collection_name):
        store.client.delete_collection(collection_name)

    store.create_collection(
        collection_name=collection_name
    )

    collections = (
        store.client
        .get_collections()
        .collections
    )

    names = [
        collection.name
        for collection in collections
    ]

    assert collection_name in names