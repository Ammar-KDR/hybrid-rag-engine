from pathlib import Path
from rag.ingestion.chunk_store import ChunkStore
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
from rag.generation.generator import (
    LMStudioGenerationService,
    OllamaGenerationService,
)
from rag.generation.prompt import PromptBuilder
from sentence_transformers import CrossEncoder
from rag.verification.pipeline import AnswerVerificationPipeline
from rag.verification.claim_extractor import GeminiClaimExtractor
from rag.verification.citation_verifier import GeminiCitationVerifier
from rag.verification.metrics import CitationMetricsCalculator
from rag.verification.faithfulness import FaithfulnessEvaluator
from rag.verification.faithfulness_verifier import GeminiFaithfulnessVerifier
from rag.verification.abstention import AbstentionPolicy
from rag.verification.runner import CitationVerificationRunner
from rag.verification.citation_verifier import LMStudioCitationVerifier
from rag.verification.claim_extractor import LMStudioClaimExtractor
from rag.verification.faithfulness_verifier import LMStudioFaithfulnessVerifier
from rag.config import settings


VERIFICATION_MODEL = (
    settings.OLLAMA_MODEL
    if settings.LLM_BACKEND == "ollama"
    else settings.LM_STUDIO_MODEL
)
CHUNK_STORE_PATH = settings.CHUNK_STORE_PATH


def create_rag_pipeline() -> RAGPipeline:
    embedding_service = EmbeddingService(
        model_name=settings.EMBEDDING_MODEL_NAME
    )

    if settings.QDRANT_STORAGE_MODE == "local":
        vector_store = QdrantVectorStore(path=settings.QDRANT_LOCAL_PATH)
    else:
        vector_store = QdrantVectorStore(url=settings.QDRANT_URL)

    rrf = ReciprocalRankFusion()

    dense_retriever = DenseRetriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        collection_name=settings.QDRANT_COLLECTION,
    )
    chunk_store = ChunkStore(CHUNK_STORE_PATH)

    chunks = chunk_store.load_all()

    if not chunks:
        raise RuntimeError(
            "Chunk index is missing or empty. "
            "Run 'python scripts/build_index.py' "
            "before starting the application."
        )
    bm25_retriever = BM25Retriever(chunks=chunks)

    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        fusion=rrf,
        candidate_k=20,
    )

    cross_encoder = CrossEncoderReranker(
        model=CrossEncoder(settings.RERANKER_MODEL_NAME)
    )

    rank_fusion_reranker = RankFusionReranker(
        reranker=cross_encoder,
        retrieval_weight=0.5,
        reranker_weight=0.5,
        rrf_k=60,
    )

    # --------------------------------------------------
    # Select generator based on LLM_BACKEND
    # --------------------------------------------------
    if settings.LLM_BACKEND == "ollama":
        generator = OllamaGenerationService(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
    elif settings.LLM_BACKEND == "gemini":
        from rag.generation.generator import GeminiGenerationService
        generator = GeminiGenerationService()
    else:
        generator = LMStudioGenerationService(
            model=settings.LM_STUDIO_MODEL,
            base_url=settings.LM_STUDIO_BASE_URL,
        )

    # --------------------------------------------------
    # Verification Pipeline (enabled conditionally)
    # --------------------------------------------------
    if settings.ENABLE_VERIFICATION:
        if settings.LLM_BACKEND == "ollama":
            claim_extractor = LMStudioClaimExtractor(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
            )
            citation_verifier = LMStudioCitationVerifier(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
            )
            faithfulness_verifier = LMStudioFaithfulnessVerifier(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
            )
        elif settings.LLM_BACKEND == "gemini":
            claim_extractor = GeminiClaimExtractor()
            citation_verifier = GeminiCitationVerifier()
            faithfulness_verifier = GeminiFaithfulnessVerifier()
        else:
            claim_extractor = LMStudioClaimExtractor(model=VERIFICATION_MODEL)
            citation_verifier = LMStudioCitationVerifier(model=VERIFICATION_MODEL)
            faithfulness_verifier = LMStudioFaithfulnessVerifier(model=VERIFICATION_MODEL)

        citation_runner = CitationVerificationRunner(verifier=citation_verifier)
        metrics_calculator = CitationMetricsCalculator()
        faithfulness_evaluator = FaithfulnessEvaluator(verifier=faithfulness_verifier)
        abstention_policy = AbstentionPolicy()

        verification_pipeline = AnswerVerificationPipeline(
            claim_extractor=claim_extractor,
            citation_runner=citation_runner,
            metrics_calculator=metrics_calculator,
            faithfulness_evaluator=faithfulness_evaluator,
            abstention_policy=abstention_policy,
        )
    else:
        verification_pipeline = None

    pipeline = RAGPipeline(
        retriever=hybrid_retriever,
        reranker=rank_fusion_reranker,
        context_builder=ContextBuilder(final_context_k=5),
        prompt_builder=PromptBuilder(),
        generator=generator,
        answer_builder=AnswerBuilder(),
        verification_pipeline=verification_pipeline,
        candidate_k=20,
        enable_verification=settings.ENABLE_VERIFICATION,
    )

    return pipeline