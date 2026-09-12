import uuid

from rag.vector_store.qdrant import QdrantVectorStore


class FakeQdrantClient:
    def __init__(self):
        self.points = []

    def upsert(
        self,
        collection_name,
        points,
    ):
        self.points.extend(points)


def test_same_chunk_id_produces_same_qdrant_point_id():
    store = QdrantVectorStore.__new__(
        QdrantVectorStore
    )

    store.client = FakeQdrantClient()

    chunk_id = "abc123"

    first_id = store.add_point(
        collection_name="test",
        chunk_id=chunk_id,
        vector=[0.1, 0.2],
        payload={"text": "hello"},
    )

    second_id = store.add_point(
        collection_name="test",
        chunk_id=chunk_id,
        vector=[0.1, 0.2],
        payload={"text": "hello"},
    )

    expected = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            chunk_id,
        )
    )

    assert first_id == expected
    assert second_id == expected
    assert first_id == second_id