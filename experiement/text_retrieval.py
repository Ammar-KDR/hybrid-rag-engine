from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore
from rag.retrieval.Dense_retrieval import DenseRetriever

embd=EmbeddingService()
qv=QdrantVectorStore()
c=DenseRetriever(embd,qv,"test_insert")
cc=c.retrieve("How can I recover a failed Kubernetes workload?")
print(cc)