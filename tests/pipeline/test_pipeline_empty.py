from unittest.mock import MagicMock
from rag.pipeline import RAGPipeline
from rag.generation.context_builder import ContextBuilder
from rag.generation.prompt import PromptBuilder
from rag.generation.answer_builder import AnswerBuilder


def test_pipeline_immediate_abstention_on_empty_retrieval():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []

    mock_reranker = MagicMock()
    mock_generator = MagicMock()

    pipeline = RAGPipeline(
        retriever=mock_retriever,
        reranker=mock_reranker,
        context_builder=ContextBuilder(final_context_k=5),
        prompt_builder=PromptBuilder(),
        generator=mock_generator,
        answer_builder=AnswerBuilder(),
        verification_pipeline=None,
        candidate_k=20,
        enable_verification=False,
    )

    result = pipeline.run("What are the system specifications?")

    assert result.candidate_count == 0
    assert result.evidence_count == 0
    assert "empty or contains no relevant documents" in result.answer.answer
    assert result.verified_answer.final_answer == result.answer.answer

    # Ensure reranker and generator were NOT called, saving compute and latency
    mock_reranker.rerank.assert_not_called()
    mock_generator.generate.assert_not_called()
