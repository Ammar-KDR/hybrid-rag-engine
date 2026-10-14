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



from rag.nlp.arabic import is_arabic_text
from rag.retrieval.model import RetrievalFilter
from rag.retrieval.service_router import ServiceRouter, RouteResult
from rag.generation.service_context_builder import ServiceContextBuilder


@dataclass
class RAGPipelineResult:
    answer: GeneratedAnswer
    verified_answer: VerifiedAnswer

    retrieval_latency_ms: float
    reranking_latency_ms: float
    generation_latency_ms: float
    verification_latency_ms: float
    total_latency_ms: float

    candidate_count: int
    evidence_count: int
    candidates: list
    reranked_chunks: list
    route_result: RouteResult | None = None


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
        service_router: ServiceRouter | None = None,
        service_context_builder: ServiceContextBuilder | None = None,
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
        self.service_router = service_router
        self.service_context_builder = service_context_builder


    def run(
        self,
        question: str,
        filter=None,
        history=None,
    ) -> RAGPipelineResult:

        if not question.strip():
            raise ValueError("question cannot be empty")

        total_start = time.perf_counter()

        # --------------------------------------------------
        # 0. Service Routing (GOV_SERVICE_MODE)
        # --------------------------------------------------
        route_res: RouteResult | None = None
        active_filter = filter

        if settings.GOV_SERVICE_MODE and self.service_router is not None:
            # If caller didn't pass explicit service_ids, route automatically
            if filter is None or not getattr(filter, "service_ids", None):
                route_res = self.service_router.route(question, history=history)
                if route_res.service_ids:
                    doc_ids = getattr(filter, "document_ids", ()) if filter else ()
                    active_filter = RetrievalFilter(
                        document_ids=doc_ids,
                        service_ids=route_res.service_ids,
                    )

        # --------------------------------------------------
        # 1. Retrieval
        # --------------------------------------------------

        retrieval_start = time.perf_counter()

        candidates = self.retriever.retrieve(
            query=question,
            top_k=self.candidate_k,
            filter=active_filter,
        )

        retrieval_latency_ms = (
            time.perf_counter() - retrieval_start
        ) * 1000

        if not candidates:
            empty_msg = (
                "لم أجد في الوثائق المتاحة ما يحدد ذلك."
                if is_arabic_text(question)
                else "The knowledge base is currently empty or contains no relevant documents."
            )
            empty_answer = GeneratedAnswer(
                question=question,
                answer=empty_msg,
                citations=[],
                unresolved_references=[],
                evidence=[],
                model="empty-pass",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=0.0,
            )
            verified_answer = self._create_fast_verified_answer(
                empty_answer
            )
            total_latency_ms = (
                time.perf_counter() - total_start
            ) * 1000

            return RAGPipelineResult(
                answer=empty_answer,
                verified_answer=verified_answer,
                retrieval_latency_ms=retrieval_latency_ms,
                reranking_latency_ms=0.0,
                generation_latency_ms=0.0,
                verification_latency_ms=0.0,
                total_latency_ms=total_latency_ms,
                candidate_count=0,
                evidence_count=0,
                candidates=[],
                reranked_chunks=[],
                route_result=route_res,
            )

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
        # 3. Context construction (Service-Aware or General)
        # --------------------------------------------------

        if (
            settings.GOV_SERVICE_MODE
            and self.service_context_builder is not None
            and route_res is not None
            and route_res.routed_services
        ):
            if len(route_res.routed_services) >= 2:
                context = self.service_context_builder.build_comparison(
                    route_res.routed_services, question
                )
            else:
                context = self.service_context_builder.build_from_service(
                    route_res.primary_service, question, reranked_chunks
                )
        else:
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
            route_result=route_res,
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
        ans_lower = generated_answer.answer.lower()
        is_insufficient = (
            "insufficient" in ans_lower
            or "available evidence" in ans_lower
            or "not enough evidence" in ans_lower
            or "غير كافية" in generated_answer.answer
            or "غير كافٍ" in generated_answer.answer
            or "لا توجد أدلة" in generated_answer.answer
            or "لا توجد معلومات" in generated_answer.answer
            or "empty or contains no relevant documents" in ans_lower
        )
        should_abstain = is_insufficient

        abstention = AbstentionDecision(
            should_abstain=should_abstain,
            reasons=["Insufficient evidence to answer question."] if should_abstain else [],
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
            decision=AbstentionDecisionType.ABSTAIN if should_abstain else AbstentionDecisionType.ACCEPT,
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