from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from rag.vector_store.qdrant import QdrantVectorStore
from rag.embedding.service import EmbeddingService


def test_metadata_filter():

    collection = "test_filter"

    store = QdrantVectorStore()

    if store.client.collection_exists(collection):
        store.client.delete_collection(collection)

    store.create_collection(
        collection_name=collection
    )

    embedder = EmbeddingService()


    documents = [
        (
            "Kubernetes pods contain containers",
            "engineering",
        ),
        (
            "Employees receive annual vacation",
            "hr",
        ),
    ]


    for index, (text, category) in enumerate(documents):

        vector = embedder.embed_text(text)

        store.add_point(
            collection_name=collection,
            chunk_id=f"chunk_{index}",
            vector=vector,
            payload={
                "text": text,
                "category": category,
            },
        )


    query_vector = embedder.embed_text(
        "How do Kubernetes containers work?"
    )


    results = store.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=1,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="category",
                    match=MatchValue(
                        value="engineering"
                    ),
                )
            ]
        ),
    )


    assert len(results) == 1

    assert (
        results[0]
        .payload["category"]
        ==
        "engineering"
    )