from rag.ingestion.pipeline import build_chunks
from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.fusion import ReciprocalRankFusion
from rag.vector_store.qdrant import QdrantVectorStore
from rag.embedding.service import EmbeddingService
from rag.pipeline import RAGPipeline
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.reranking.reranker import CrossEncoderReranker
from rag.reranking.rank_fusion_reranker import RankFusionReranker
from rag.generation.answer_builder import AnswerBuilder
from rag.generation.context_builder import ContextBuilder
from rag.generation.generator import GeminiGenerationService
from rag.generation.prompt import PromptBuilder
from sentence_transformers import CrossEncoder


def create_rag_pipeline() -> RAGPipeline:
    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()
    rrf=ReciprocalRankFusion()

    dense_retriever = DenseRetriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        collection_name="documents3",
    )

    bm25_retriever = BM25Retriever(
        chunks=build_chunks()
    )

    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        fusion=rrf
        ,candidate_k=20
    )

    cross_encoder = CrossEncoderReranker(
        model=CrossEncoder("BAAI/bge-reranker-base")
    )

    rank_fusion_reranker = RankFusionReranker(
        reranker=cross_encoder,
        retrieval_weight=0.5,
        reranker_weight=0.5,
        rrf_k=60,
    )

    pipeline = RAGPipeline(
        retriever=hybrid_retriever,
        reranker=rank_fusion_reranker,
        context_builder=ContextBuilder(final_context_k=5),
        prompt_builder=PromptBuilder(),
        generator=GeminiGenerationService(
            model="gemini-3.5-flash"
        ),
        answer_builder=AnswerBuilder(),
        candidate_k=20,
    )

    return pipeline