from rag.vector_store.qdrant import QdrantVectorStore
from rag.embedding.service import EmbeddingService
from rag.deduplication.detector import DuplicateDetector


def setup_collection(collection_name):
    store = QdrantVectorStore()

    if store.client.collection_exists(collection_name):
        store.client.delete_collection(collection_name)

    store.create_collection(
        collection_name=collection_name
    )

    return store


def test_exact_duplicate_detection():

    collection = "test_exact_duplicate"

    store = setup_collection(collection)

    embedder = EmbeddingService()

    original_text = (
        "Kubernetes pods contain containers"
    )

    original_vector = embedder.embed_text(
        original_text
    )

    store.add_point(
        collection_name=collection,
        chunk_id="original",
        vector=original_vector,
        payload={
            "text": original_text
        },
    )

    detector = DuplicateDetector(
        vector_store=store,
        threshold=0.95,
    )

    duplicate_vector = embedder.embed_text(
        "Kubernetes pods contain containers"
    )

    assert detector.is_duplicate(
        collection_name=collection,
        vector=duplicate_vector,
    )


def test_similar_but_not_duplicate():

    collection = "test_similar_not_duplicate"

    store = setup_collection(collection)

    embedder = EmbeddingService()

    original_text = (
        "Kubernetes pods contain containers"
    )

    original_vector = embedder.embed_text(
        original_text
    )

    store.add_point(
        collection_name=collection,
        chunk_id="original",
        vector=original_vector,
        payload={
            "text": original_text
        },
    )

    detector = DuplicateDetector(
        vector_store=store,
        threshold=0.95,
    )

    similar_vector = embedder.embed_text(
        "Pods are Kubernetes units that run containers"
    )

    assert not detector.is_duplicate(
        collection_name=collection,
        vector=similar_vector,
    )