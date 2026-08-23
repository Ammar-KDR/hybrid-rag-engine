from rag.embedding.service import EmbeddingService
from .model import RetrievedChunk



class DenseRetriever:
    def __init__(self,embedding_service,vector_store,collection_name: str,):

        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.collection_name = collection_name

    def retrieve(self,query:str,top_k=5,filter=None):

        
        query_vector=self.embedding_service.embed_text(query)
        qdrant_points=self.vector_store.search(self.collection_name,query_vector,top_k,filter)
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
            

        



