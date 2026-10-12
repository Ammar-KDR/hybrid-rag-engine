from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue
from rag.embedding.service import EmbeddingService
from .model import RetrievedChunk, RetrievalFilter



class DenseRetriever:
    def __init__(self, embedding_service, vector_store, collection_name: str):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.collection_name = collection_name

    def retrieve(self, query: str, top_k: int = 5, filter=None):
        query_vector = self.embedding_service.embed_text(query)

        qdrant_filter = None
        if isinstance(filter, Filter):
            qdrant_filter = filter
        elif filter is not None and getattr(filter, "document_ids", None):
            doc_ids = list(filter.document_ids)
            if len(doc_ids) == 1:
                qdrant_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=doc_ids[0]),
                        )
                    ]
                )
            elif len(doc_ids) > 1:
                qdrant_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchAny(any=doc_ids),
                        )
                    ]
                )

        qdrant_points = self.vector_store.search(
            self.collection_name,
            query_vector,
            top_k,
            qdrant_filter,
        )
        r_chunks=[]
        rank=1
        for qp in qdrant_points:
            metadata = {
                key: value
                for key, value in qp.payload.items()
                if key not in {"chunk_id", "text"}
            }
            
            r_chunk=RetrievedChunk(
                chunk_id=qp.payload["chunk_id"],
                text=qp.payload["text"],
                metadata=metadata,
                score=qp.score,
                rank=rank
                )
            rank+=1
            r_chunks.append(r_chunk)
        return r_chunks
            

        



