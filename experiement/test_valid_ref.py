from rag.generation.model import GenerationResult
from rag.generation.context_builder import ContextBuilder
from rag.generation.answer_builder import AnswerBuilder
from rag.reranking.model import RerankedChunk


def make_chunk(
    chunk_id: str,
    text: str,
    source: str = "kubernetes.md",
    final_rank: int = 1,
) -> RerankedChunk:

    return RerankedChunk(
        chunk_id=chunk_id,
        text=text,
        metadata={
            "source": source,
            "file_type": "md",
        },
        retrieval_score=0.8,
        retrieval_rank=final_rank,
        reranker_score=0.9,
        reranked_rank=final_rank,
        final_score=0.85,
        final_rank=final_rank,
    )
def test_answer_builder_maps_valid_reference():

    generation = GenerationResult(
        text="Use the restart command. [1]",
        model="fake-model",
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        latency_ms=10,
    )

    context = ContextBuilder().build([
        make_chunk(
            chunk_id="chunk-1",
            text="Restart command evidence.",
        )
    ])

    answer = AnswerBuilder().build(
        question="How do I restart it?",
        generation=generation,
        context=context,
    )

    assert len(answer.citations) == 1
    assert answer.citations[0].reference == 1
    assert answer.citations[0].chunk_id == "chunk-1"

    assert answer.unresolved_references == []

def test_answer_builder_records_unresolved_reference():

    generation = GenerationResult(
        text="Use the restart command. [1][7]",
        model="fake-model",
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        latency_ms=10,
    )

    context = ContextBuilder().build([
        make_chunk(
            chunk_id="chunk-1",
            text="Restart command evidence.",
        )
    ])

    answer = AnswerBuilder().build(
        question="How do I restart it?",
        generation=generation,
        context=context,
    )

    assert len(answer.citations) == 1
    assert answer.citations[0].reference == 1

    assert answer.unresolved_references == [7]