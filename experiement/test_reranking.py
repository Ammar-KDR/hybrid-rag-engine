import pytest

from rag.retrieval.model import RetrievedChunk
from rag.reranking.reranker import CrossEncoderReranker


class FakeCrossEncoder:
    """
    Fake model used to test reranking logic without loading
    the real transformer model.

    Scores correspond to candidates in the same order
    they are passed to predict().
    """

    def predict(self, pairs):
        return [0.2, 8.0, 1.5]


@pytest.fixture
def candidates():
    return [
        RetrievedChunk(
            chunk_id="a",
            text="chunk A",
            metadata={"source": "a.md"},
            score=0.9,
            rank=1,
        ),
        RetrievedChunk(
            chunk_id="b",
            text="chunk B",
            metadata={"source": "b.md"},
            score=0.8,
            rank=2,
        ),
        RetrievedChunk(
            chunk_id="c",
            text="chunk C",
            metadata={"source": "c.md"},
            score=0.7,
            rank=3,
        ),
    ]


@pytest.fixture
def reranker():
    model = FakeCrossEncoder()
    return CrossEncoderReranker(model)


def test_reranker_sorts_by_cross_encoder_score(
    reranker,
    candidates,
):
    results = reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=3,
    )

    assert len(results) == 3

    assert results[0].chunk_id == "b"
    assert results[1].chunk_id == "c"
    assert results[2].chunk_id == "a"

    assert results[0].reranked_rank == 1
    assert results[1].reranked_rank == 2
    assert results[2].reranked_rank == 3


def test_reranker_preserves_retrieval_provenance(
    reranker,
    candidates,
):
    results = reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=3,
    )

    first_result = results[0]

    # Candidate B was originally rank 2
    assert first_result.chunk_id == "b"

    # Original retrieval information must remain intact
    assert first_result.retrieval_rank == 2
    assert first_result.retrieval_score == 0.8

    # New reranking information
    assert first_result.reranker_score == 8.0
    assert first_result.reranked_rank == 1

    # Original metadata should also survive
    assert first_result.metadata == {"source": "b.md"}


def test_reranker_respects_top_k(
    reranker,
    candidates,
):
    results = reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=2,
    )

    assert len(results) == 2

    assert results[0].chunk_id == "b"
    assert results[1].chunk_id == "c"

    assert results[0].reranked_rank == 1
    assert results[1].reranked_rank == 2


def test_top_k_larger_than_candidates_returns_all(
    reranker,
    candidates,
):
    results = reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=10,
    )

    assert len(results) == 3

    assert results[0].chunk_id == "b"
    assert results[1].chunk_id == "c"
    assert results[2].chunk_id == "a"


def test_reranker_returns_empty_list_for_empty_candidates():
    model = FakeCrossEncoder()
    reranker = CrossEncoderReranker(model)

    results = reranker.rerank(
        query="test query",
        candidates=[],
        top_k=5,
    )

    assert results == []


def test_reranker_rejects_empty_query(
    reranker,
    candidates,
):
    with pytest.raises(ValueError):
        reranker.rerank(
            query="",
            candidates=candidates,
            top_k=5,
        )


def test_reranker_rejects_whitespace_query(
    reranker,
    candidates,
):
    with pytest.raises(ValueError):
        reranker.rerank(
            query="     ",
            candidates=candidates,
            top_k=5,
        )


def test_reranker_rejects_zero_top_k(
    reranker,
    candidates,
):
    with pytest.raises(ValueError):
        reranker.rerank(
            query="test query",
            candidates=candidates,
            top_k=0,
        )


def test_reranker_rejects_negative_top_k(
    reranker,
    candidates,
):
    with pytest.raises(ValueError):
        reranker.rerank(
            query="test query",
            candidates=candidates,
            top_k=-1,
        )