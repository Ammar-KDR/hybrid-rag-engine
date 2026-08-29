import time
from dataclasses import dataclass
from rag.generation.model import GeneratedAnswer
from rag.generation.answer_builder import AnswerBuilder
from rag.generation.context_builder import ContextBuilder
from rag.generation.generator import GeminiGenerationService
from rag.generation.prompt import PromptBuilder



@dataclass
class RAGPipelineResult:
    answer: GeneratedAnswer

    retrieval_latency_ms: float
    reranking_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float

    candidate_count: int
    evidence_count: int

class RAGPipeline:

    def __init__(
        self,
        retriever,
        reranker,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        generator: GeminiGenerationService,
        answer_builder: AnswerBuilder,
        candidate_k: int = 20,
    ):
        self.retriever = retriever
        self.reranker = reranker

        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.generator = generator
        self.answer_builder = answer_builder

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

        answer = self.answer_builder.build(
            question=question,
            generation=generation,
            context=context,
        )


        # --------------------------------------------------
        # 7. Final observability
        # --------------------------------------------------

        total_latency_ms = (
            time.perf_counter() - total_start
        ) * 1000

        return RAGPipelineResult(
            answer=answer,

            retrieval_latency_ms=retrieval_latency_ms,
            reranking_latency_ms=reranking_latency_ms,
            generation_latency_ms=generation.latency_ms,
            total_latency_ms=total_latency_ms,

            candidate_count=len(candidates),
            evidence_count=len(context.blocks),
        )