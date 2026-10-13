import pytest
from rag.generation.context_builder import ContextBuilder
from rag.reranking.model import RerankedChunk


def make_chunk(chunk_id: str, text: str, reranker_score: float, final_score: float = 0.0, source: str = "doc.pdf"):
    return RerankedChunk(
        chunk_id=chunk_id,
        text=text,
        metadata={"source": source, "page_number": 1, "heading_path": ["Header"]},
        retrieval_score=0.5,
        retrieval_rank=1,
        reranker_score=reranker_score,
        reranked_rank=1,
        final_score=final_score,
        final_rank=1,
    )


def test_context_builder_filters_distant_noise_chunks():
    builder = ContextBuilder(
        final_context_k=5,
        min_score_threshold=0.01,
        relative_threshold_ratio=0.08,
    )

    chunks = [
        make_chunk("c1", "Vehicle licensing technical inspection requirements", 0.88, source="vehicle.pdf"),
        make_chunk("c2", "Vehicle licensing inspection fees 10 JOD", 0.08, source="vehicle.pdf"),
        make_chunk("c3", "Application server troubleshooting health checks", 0.002, source="trouble.md"),
        make_chunk("c4", "Building permits regulations and engineering drawings", 0.001, source="building.pdf"),
        make_chunk("c5", "Civil status smart card and passport requirements", 0.001, source="civil_status.pdf"),
    ]

    context = builder.build(chunks)

    # Chunks 3, 4, 5 must be eliminated as noise
    assert len(context.blocks) == 2
    assert context.blocks[0].chunk_id == "c1"
    assert context.blocks[1].chunk_id == "c2"
    assert context.blocks[0].source == "vehicle.pdf"
    assert context.blocks[1].source == "vehicle.pdf"
    assert "trouble.md" not in context.text
    assert "civil_status.pdf" not in context.text


def test_context_builder_retains_close_candidates():
    builder = ContextBuilder(
        final_context_k=3,
        min_score_threshold=0.01,
        relative_threshold_ratio=0.1,
    )

    chunks = [
        make_chunk("c1", "Text 1", 0.80),
        make_chunk("c2", "Text 2", 0.70),
        make_chunk("c3", "Text 3", 0.50),
        make_chunk("c4", "Text 4", 0.40),
    ]

    context = builder.build(chunks)
    assert len(context.blocks) == 3
    assert [b.chunk_id for b in context.blocks] == ["c1", "c2", "c3"]


def test_context_builder_preserves_at_least_top_candidate():
    builder = ContextBuilder(
        final_context_k=5,
        min_score_threshold=0.05,
    )

    chunks = [
        make_chunk("c1", "Low confidence top match", 0.004),
        make_chunk("c2", "Even lower match", 0.001),
    ]

    context = builder.build(chunks)
    assert len(context.blocks) == 1
    assert context.blocks[0].chunk_id == "c1"


def test_context_builder_empty():
    builder = ContextBuilder(final_context_k=5)
    context = builder.build([])
    assert context.text == ""
    assert context.blocks == []
