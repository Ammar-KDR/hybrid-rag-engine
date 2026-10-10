import time
from dataclasses import dataclass
from rag.generation.model import GeneratedAnswer
from rag.generation.answer_builder import AnswerBuilder
from rag.generation.context_builder import ContextBuilder
from rag.generation.generator import GeminiGenerationService
from rag.generation.prompt import PromptBuilder
from rag.config import settings
from rag.verification.model import (
    VerifiedAnswer,
    ClaimExtractionResult,
    CitationVerificationResult,
    CitationMetrics,
    FaithfulnessSummary,
    AbstentionDecision,
    AbstentionSignals,
    AbstentionDecisionType,
)
from rag.verification.pipeline import AnswerVerificationPipeline



@dataclass
class RAGPipelineResult:
    answer: GeneratedAnswer
    verified_answer:VerifiedAnswer

    retrieval_latency_ms: float
    reranking_latency_ms: float
    generation_latency_ms: float
    verification_latency_ms: float
    total_latency_ms: float


    candidate_count: int
    evidence_count: int
    candidates: list
    reranked_chunks: list


class RAGPipeline:

    def __init__(
        self,
        retriever,
        reranker,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        generator,
        answer_builder: AnswerBuilder,
        verification_pipeline: AnswerVerificationPipeline | None = None,
        candidate_k: int = 20,
        enable_verification: bool | None = None,
    ):
        self.retriever = retriever
        self.reranker = reranker

        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.generator = generator
        self.answer_builder = answer_builder
        self.verification_pipeline = verification_pipeline
        self.enable_verification = (
            enable_verification
            if enable_verification is not None
            else settings.ENABLE_VERIFICATION
        )

        self.candidate_k = candidate_k


    def run(
        self,
        question: str,
    ) -> RAGPipelineResult:


        if not question.strip():
            raise ValueError("question cannot be empty")

        total_start = time.perf_counter()

        # --------------------------------------------------
        # 1. Retrieval
        # --------------------------------------------------

        retrieval_start = time.perf_counter()

        candidates = self.retriever.retrieve(
            query=question,
            top_k=self.candidate_k,
        )

        retrieval_latency_ms = (
            time.perf_counter() - retrieval_start
        ) * 1000


        # --------------------------------------------------
        # 2. Reranking
        # --------------------------------------------------

        reranking_start = time.perf_counter()

        reranked_chunks = self.reranker.rerank(
            query=question,
            candidates=candidates,
        )

        reranking_latency_ms = (
            time.perf_counter() - reranking_start
        ) * 1000


        # --------------------------------------------------
        # 3. Context construction
        # --------------------------------------------------

        context = self.context_builder.build(
            reranked_chunks
        )


        # --------------------------------------------------
        # 4. Prompt construction
        # --------------------------------------------------

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
        )


        # --------------------------------------------------
        # 5. Generation
        # --------------------------------------------------

        generation = self.generator.generate(
            prompt
        )


        # --------------------------------------------------
        # 6. Answer + citation mapping
        # --------------------------------------------------

        generated_answer = self.answer_builder.build(
            question=question,
            generation=generation,
            context=context,
        )


        
        # --------------------------------------------------
        # 7. Verification (Conditional based on enable_verification)
        # --------------------------------------------------

        if self.enable_verification and self.verification_pipeline is not None:
            verified_answer = self.verification_pipeline.verify(
                generated_answer
            )
        else:
            verified_answer = self._create_fast_verified_answer(
                generated_answer
            )



        # --------------------------------------------------
        # 8. Final observability
        # --------------------------------------------------

        total_latency_ms = (
            time.perf_counter() - total_start
        ) * 1000


        return RAGPipelineResult(
            answer=generated_answer,
            verified_answer=verified_answer,

            retrieval_latency_ms=retrieval_latency_ms,
            reranking_latency_ms=reranking_latency_ms,
            generation_latency_ms=generation.latency_ms,
            verification_latency_ms=(
                verified_answer.verification_latency_ms
            ),
            total_latency_ms=total_latency_ms,

            candidate_count=len(candidates),
            evidence_count=len(context.blocks),
            candidates=candidates,
            reranked_chunks=reranked_chunks,
        )

    @staticmethod
    def _create_fast_verified_answer(
        generated_answer: GeneratedAnswer,
    ) -> VerifiedAnswer:
        claims = ClaimExtractionResult(
            claims=[],
            invalid_references=[],
            model="fast-pass",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            latency_ms=0.0,
        )
        citation_verification = CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[],
        )
        has_citations = len(generated_answer.citations) > 0
        citation_metrics = CitationMetrics(
            citation_precision=1.0 if has_citations else None,
            citation_coverage=1.0 if has_citations else None,
            total_verifications=0,
            supported_verifications=0,
            partially_supported_verifications=0,
            unsupported_verifications=0,
            contradicted_verifications=0,
            total_claims=0,
            adequately_cited_claims=0,
            uncited_claims=0,
        )
        faithfulness = FaithfulnessSummary(
            claim_results=[],
            total_claims=0,
            supported_claims=0,
            partially_supported_claims=0,
            unsupported_claims=0,
            contradicted_claims=0,
        )
        abstention = AbstentionDecision(
            should_abstain=False,
            reasons=[],
            signals=AbstentionSignals(
                total_claims=0,
                supported_claims=0,
                partially_supported_claims=0,
                unsupported_claims=0,
                contradicted_claims=0,
                uncited_claims=0,
                unresolved_references=0,
                citation_precision=1.0 if has_citations else None,
                citation_coverage=1.0 if has_citations else None,
                faithfulness_score=1.0,
                supported_ratio=1.0,
                partially_supported_ratio=0.0,
                unsupported_ratio=0.0,
                contradicted_ratio=0.0,
            ),
            decision=AbstentionDecisionType.ACCEPT,
        )
        return VerifiedAnswer(
            generated_answer=generated_answer,
            claims=claims,
            citation_verification=citation_verification,
            citation_metrics=citation_metrics,
            faithfulness=faithfulness,
            final_answer=generated_answer.answer,
            abstention=abstention,
            verification_latency_ms=0.0,
        )