from qdrant_client import QdrantClient


def inspect_chunks(
    collection_name: str = "documents",
    host: str = "localhost",
    port: int = 6333,
    limit: int = 20,
):
    client = QdrantClient(
        host=host,
        port=port,
    )

    results = client.scroll(
        collection_name=collection_name,
        with_payload=True,
        with_vectors=False,
    )

    points, _ = results

    for point in points:
        payload = point.payload or {}

        print(payload["chunk_id"])
        print(payload["source"])
        print(payload["heading"])


if __name__ == "__main__":
    inspect_chunks()