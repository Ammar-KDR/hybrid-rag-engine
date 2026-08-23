from pathlib import Path
import json

from qdrant_client import QdrantClient


COLLECTION_NAME = "documents"
OUTPUT_FILE = Path("data/evaluation/chunks.json")


def export_chunks(
    host: str = "localhost",
    port: int = 6333,
    limit: int = 1000,
):
    client = QdrantClient(
        host=host,
        port=port,
    )

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    chunks = []

    for point in points:
        payload = point.payload or {}

        chunks.append(
            {
                "chunk_id": payload.get("chunk_id"),
                "source": payload.get("source"),
                "heading": payload.get("heading"),
                "metadata": {
                    key: value
                    for key, value in payload.items()
                    if key not in {
                        "chunk_id",
                        "text",
                    }
                },
                "text": payload.get("text", ""),
            }
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            chunks,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(
        f"Exported {len(chunks)} chunks"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    export_chunks()