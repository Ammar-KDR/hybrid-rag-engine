from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams,PointStruct
import uuid
from qdrant_client.models import Filter, FieldCondition, MatchValue


class QdrantVectorStore:
    def __init__(
        self,
        url: str | None = None,
        path: str | Path | None = None,
    ):
        if path is not None:
            Path(path).mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(path))
        else:
            self.client = QdrantClient(
                url=url or "http://localhost:6333"
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
    def add_points(
        self,
        collection_name: str,
        items: list[tuple[str, list[float], dict]],
        batch_size: int = 128,
    ) -> list[str]:
        point_ids = []
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            points = []
            for chunk_id, vector, payload in batch:
                point_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        chunk_id,
                    )
                )
                point_ids.append(point_id)
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "chunk_id": chunk_id,
                            **payload,
                        },
                    )
                )
            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
        return point_ids

    def add_point(
        self,
        collection_name: str,
        chunk_id: str,
        vector: list[float],
        payload: dict,
    ):
        return self.add_points(
            collection_name=collection_name,
            items=[(chunk_id, vector, payload)],
        )[0]
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