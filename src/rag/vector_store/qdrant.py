from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams,PointStruct
import uuid
from qdrant_client.models import Filter, FieldCondition, MatchValue


class QdrantVectorStore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
    ):
        self.client = QdrantClient(
            host=host,
            port=port,
        )
    def create_collection(
        self,
        collection_name: str = "documents",
        vector_size: int = 384,
    ):

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
    def add_point(
    self,
    collection_name: str,
    chunk_id: str,
    vector: list[float],
    payload: dict,
    ):
        point_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            chunk_id,
            )
        )
        point = PointStruct(
            id=point_id,
            vector=vector,
            payload={
            "chunk_id": chunk_id,
            **payload,
        },
        )

        self.client.upsert(
            collection_name=collection_name,
            points=[point],
        )

        return point.id
    def search(
    self,
    collection_name: str,
    query_vector: list[float],
    limit: int = 5,
    query_filter: Filter | None = None,
    ):

        results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                query_filter=query_filter,
            )

        return results.points
    def reset_collection(
        self,
        collection_name: str,
        vector_size: int = 384,
    ) -> None:

        if self.client.collection_exists(
            collection_name=collection_name
        ):
            self.client.delete_collection(
                collection_name=collection_name
            )

        self.create_collection(
            collection_name=collection_name,
            vector_size=vector_size,
        )