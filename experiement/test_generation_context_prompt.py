import pytest

from rag.reranking.model import RerankedChunk
from rag.generation.context_builder import ContextBuilder
from rag.generation.prompt import PromptBuilder


def make_chunk(
    chunk_id: str,
    text: str,
    source: str = "kubernetes.md",
    heading_path: list[str] | None = None,
    page_number: int | None = None,
    final_rank: int = 1,
) -> RerankedChunk:

    metadata = {
        "source": source,
        "file_type": "md",
    }

    if heading_path is not None:
        metadata["heading_path"] = heading_path

    if page_number is not None:
        metadata["page_number"] = page_number

    return RerankedChunk(
        chunk_id=chunk_id,
        text=text,
        metadata=metadata,

        retrieval_score=0.8,
        retrieval_rank=final_rank,

        reranker_score=0.9,
        reranked_rank=final_rank,

        final_score=0.85,
        final_rank=final_rank,
    )


# ============================================================
# ContextBuilder Tests
# ============================================================


def test_context_builder_stable_numbering():

    chunks = [
        make_chunk(
            chunk_id="chunk-1",
            text="First evidence",
            final_rank=1,
        ),
        make_chunk(
            chunk_id="chunk-2",
            text="Second evidence",
            final_rank=2,
        ),
        make_chunk(
            chunk_id="chunk-3",
            text="Third evidence",
            final_rank=3,
        ),
    ]

    builder = ContextBuilder(final_context_k=5)

    context = builder.build(chunks)

    assert len(context.blocks) == 3

    assert context.blocks[0].reference == 1
    assert context.blocks[1].reference == 2
    assert context.blocks[2].reference == 3

    assert context.blocks[0].chunk_id == "chunk-1"
    assert context.blocks[1].chunk_id == "chunk-2"
    assert context.blocks[2].chunk_id == "chunk-3"


def test_context_builder_respects_final_context_k():

    chunks = [
        make_chunk(
            chunk_id=f"chunk-{i}",
            text=f"Evidence {i}",
            final_rank=i,
        )
        for i in range(1, 8)
    ]

    builder = ContextBuilder(final_context_k=5)

    context = builder.build(chunks)

    assert len(context.blocks) == 5

    assert [
        block.chunk_id
        for block in context.blocks
    ] == [
        "chunk-1",
        "chunk-2",
        "chunk-3",
        "chunk-4",
        "chunk-5",
    ]


def test_context_builder_preserves_metadata():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Restart the deployment.",
        source="kubernetes.md",
        heading_path=[
            "Deployments",
            "Recovery",
        ],
    )

    builder = ContextBuilder()

    context = builder.build([chunk])

    block = context.blocks[0]

    assert block.chunk_id == "chunk-1"
    assert block.source == "kubernetes.md"

    assert block.heading_path == [
        "Deployments",
        "Recovery",
    ]


def test_context_builder_handles_page_number():

    chunk = make_chunk(
        chunk_id="pdf-chunk",
        text="PDF evidence",
        source="manual.pdf",
        page_number=7,
    )

    chunk.metadata["file_type"] = "pdf"

    builder = ContextBuilder()

    context = builder.build([chunk])

    block = context.blocks[0]

    assert block.source == "manual.pdf"
    assert block.file_type == "pdf"
    assert block.page_number == 7

    assert "Page: 7" in context.text


def test_context_builder_renders_heading_path():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Use kubectl rollout restart.",
        heading_path=[
            "Kubernetes",
            "Deployments",
            "Recovery",
        ],
    )

    builder = ContextBuilder()

    context = builder.build([chunk])

    assert (
        "Section: Kubernetes > Deployments > Recovery"
        in context.text
    )


def test_context_builder_renders_evidence_markers():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Some useful evidence.",
    )

    builder = ContextBuilder()

    context = builder.build([chunk])

    assert "[EVIDENCE 1]" in context.text
    assert "[/EVIDENCE 1]" in context.text
    assert "Some useful evidence." in context.text


def test_context_builder_empty_input():

    builder = ContextBuilder()

    context = builder.build([])

    assert context.text == ""
    assert context.blocks == []


def test_get_block_returns_correct_evidence():

    chunks = [
        make_chunk(
            chunk_id="chunk-A",
            text="Evidence A",
            final_rank=1,
        ),
        make_chunk(
            chunk_id="chunk-B",
            text="Evidence B",
            final_rank=2,
        ),
    ]

    builder = ContextBuilder()

    context = builder.build(chunks)

    block = context.get_block(2)

    assert block is not None
    assert block.reference == 2
    assert block.chunk_id == "chunk-B"


def test_get_block_returns_none_for_invalid_reference():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Evidence",
    )

    context = ContextBuilder().build([chunk])

    assert context.get_block(99) is None


def test_context_builder_rejects_invalid_k():

    with pytest.raises(ValueError):
        ContextBuilder(final_context_k=0)

    with pytest.raises(ValueError):
        ContextBuilder(final_context_k=-1)


# ============================================================
# PromptBuilder Tests
# ============================================================


def test_prompt_contains_question_and_evidence():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text=(
            "To restart a Kubernetes deployment, use "
            "kubectl rollout restart deployment <name>."
        ),
        heading_path=[
            "Deployments",
            "Recovery",
        ],
    )

    context = ContextBuilder().build([chunk])

    prompt = PromptBuilder().build(
        question="How do I restart a Kubernetes deployment?",
        context=context,
    )

    assert (
        "How do I restart a Kubernetes deployment?"
        in prompt.user_prompt
    )

    assert (
        "kubectl rollout restart deployment <name>"
        in prompt.user_prompt
    )


def test_prompt_contains_evidence_reference():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Evidence text.",
    )

    context = ContextBuilder().build([chunk])

    prompt = PromptBuilder().build(
        question="What does the evidence say?",
        context=context,
    )

    assert "[EVIDENCE 1]" in prompt.user_prompt
    assert "[/EVIDENCE 1]" in prompt.user_prompt


def test_system_prompt_contains_grounding_instruction():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Evidence.",
    )

    context = ContextBuilder().build([chunk])

    prompt = PromptBuilder().build(
        question="Question?",
        context=context,
    )

    system_prompt = prompt.system_prompt.lower()

    assert "only the supplied evidence" in system_prompt


def test_system_prompt_contains_insufficient_evidence_rule():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Evidence.",
    )

    context = ContextBuilder().build([chunk])

    prompt = PromptBuilder().build(
        question="Question?",
        context=context,
    )

    assert (
        "insufficient"
        in prompt.system_prompt.lower()
    )


def test_system_prompt_treats_documents_as_data():

    chunk = make_chunk(
        chunk_id="chunk-1",
        text="Evidence.",
    )

    context = ContextBuilder().build([chunk])

    prompt = PromptBuilder().build(
        question="Question?",
        context=context,
    )

    assert (
        "data, not instructions"
        in prompt.system_prompt.lower()
    )


def test_prompt_handles_no_evidence():

    context = ContextBuilder().build([])

    prompt = PromptBuilder().build(
        question="How does AWS Lambda work?",
        context=context,
    )

    assert "[NO EVIDENCE PROVIDED]" in prompt.user_prompt


def test_prompt_rejects_empty_question():

    context = ContextBuilder().build([])

    builder = PromptBuilder()

    with pytest.raises(ValueError):
        builder.build(
            question="",
            context=context,
        )


def test_prompt_rejects_whitespace_only_question():

    context = ContextBuilder().build([])

    builder = PromptBuilder()

    with pytest.raises(ValueError):
        builder.build(
            question="    ",
            context=context,
        )