import pytest

from rag.retrieval.model import RetrievedChunk
from rag.reranking.model import RerankedChunk
from rag.reranking.rank_fusion_reranker import RankFusionReranker


# ============================================================
# FAKE CROSS-ENCODER RERANKER
# ============================================================

class FakeCrossEncoderReranker:
    """
    Deterministic fake reranker.

    ce_ranks maps:

        chunk_id -> cross-encoder rank

    Example:

        {
            "a": 5,
            "b": 1,
            "c": 3,
        }

    lets us test RankFusionReranker without loading
    the actual transformer.
    """

    def __init__(self, ce_ranks):
        self.ce_ranks = ce_ranks

    def rerank(
        self,
        query,
        candidates,
        top_k=5,
    ):

        results = []

        for candidate in candidates:

            ce_rank = self.ce_ranks[
                candidate.chunk_id
            ]

            # Arbitrary deterministic score.
            # The RankFusionReranker should NOT use this
            # raw value for fusion.
            ce_score = float(
                100 - ce_rank
            )

            result = RerankedChunk(
                chunk_id=candidate.chunk_id,
                text=candidate.text,
                metadata=candidate.metadata,

                retrieval_score=candidate.score,
                retrieval_rank=candidate.rank,

                reranker_score=ce_score,
                reranked_rank=ce_rank,

                # Pure fake CE output:
                final_score=ce_score,
                final_rank=ce_rank,
            )

            results.append(result)

        # Simulate real CrossEncoderReranker behavior:
        # highest-ranked CE result first.
        results.sort(
            key=lambda item: item.reranked_rank
        )

        return results[:top_k]


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def candidates():

    return [
        RetrievedChunk(
            chunk_id="a",
            text="Exact Docker command result",
            metadata={"source": "docker.md"},
            score=0.90,
            rank=1,
        ),
        RetrievedChunk(
            chunk_id="b",
            text="Semantic troubleshooting explanation",
            metadata={"source": "troubleshooting.md"},
            score=0.80,
            rank=2,
        ),
        RetrievedChunk(
            chunk_id="c",
            text="Another related chunk",
            metadata={"source": "other.md"},
            score=0.70,
            rank=3,
        ),
    ]


# ============================================================
# BASIC FUSION TEST
# ============================================================

def test_rank_fusion_combines_retrieval_and_reranked_rank(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 3,
            "b": 1,
            "c": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
        retrieval_weight=0.5,
        reranker_weight=0.5,
        rrf_k=60,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=3,
    )

    assert len(results) == 3

    # Candidate A:
    # retrieval rank = 1
    # CE rank        = 3
    #
    # Candidate B:
    # retrieval rank = 2
    # CE rank        = 1
    #
    # With 50/50 fusion, these should be very competitive.
    #
    # The exact order is determined by the formula,
    # so we verify scores directly below.

    result_map = {
        result.chunk_id: result
        for result in results
    }

    expected_a = (
        0.5 / (60 + 1)
        +
        0.5 / (60 + 3)
    )

    expected_b = (
        0.5 / (60 + 2)
        +
        0.5 / (60 + 1)
    )

    expected_c = (
        0.5 / (60 + 3)
        +
        0.5 / (60 + 2)
    )

    assert result_map["a"].final_score == pytest.approx(
        expected_a
    )

    assert result_map["b"].final_score == pytest.approx(
        expected_b
    )

    assert result_map["c"].final_score == pytest.approx(
        expected_c
    )


# ============================================================
# FINAL RANKS MUST MATCH FUSED SCORE
# ============================================================

def test_final_results_are_sorted_by_fused_score(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 3,
            "b": 1,
            "c": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
        retrieval_weight=0.5,
        reranker_weight=0.5,
        rrf_k=60,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=3,
    )

    assert (
        results[0].final_score
        >= results[1].final_score
    )

    assert (
        results[1].final_score
        >= results[2].final_score
    )

    assert results[0].final_rank == 1
    assert results[1].final_rank == 2
    assert results[2].final_rank == 3


# ============================================================
# PRESERVE ALL RANKING PROVENANCE
# ============================================================

def test_rank_fusion_preserves_provenance(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 3,
            "b": 1,
            "c": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
        retrieval_weight=0.5,
        reranker_weight=0.5,
        rrf_k=60,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=3,
    )

    result_map = {
        result.chunk_id: result
        for result in results
    }

    result_a = result_map["a"]

    # Stage 1
    assert result_a.retrieval_rank == 1
    assert result_a.retrieval_score == 0.90

    # Stage 2
    assert result_a.reranked_rank == 3
    assert result_a.reranker_score == 97.0

    # Stage 3
    assert result_a.final_rank >= 1
    assert result_a.final_score > 0

    # Original content preserved
    assert (
        result_a.metadata["source"]
        == "docker.md"
    )

    assert (
        result_a.text
        == "Exact Docker command result"
    )


# ============================================================
# RETRIEVAL SIGNAL SHOULD BE ABLE TO PROTECT A RESULT
# ============================================================

def test_strong_retrieval_rank_can_survive_weaker_ce_rank():

    candidates = [
        RetrievedChunk(
            chunk_id="lexical",
            text="docker images",
            metadata={},
            score=0.95,
            rank=1,
        ),
        RetrievedChunk(
            chunk_id="semantic",
            text="Docker troubleshooting information",
            metadata={},
            score=0.70,
            rank=8,
        ),
    ]

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "lexical": 5,
            "semantic": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
        retrieval_weight=0.5,
        reranker_weight=0.5,
        rrf_k=60,
    )

    results = fusion_reranker.rerank(
        query="Which command checks Docker images?",
        candidates=candidates,
        top_k=2,
    )

    # This mirrors the failure mode we observed:
    #
    # lexical:
    # retrieval rank = 1
    # CE rank        = 5
    #
    # semantic:
    # retrieval rank = 8
    # CE rank        = 2
    #
    # Fusion should prevent the strong retrieval result
    # from automatically being destroyed.

    assert results[0].chunk_id == "lexical"

    assert (
        results[0].retrieval_rank
        == 1
    )

    assert (
        results[0].reranked_rank
        == 5
    )

    assert (
        results[0].final_rank
        == 1
    )


# ============================================================
# RETRIEVAL-ONLY WEIGHT
# ============================================================

def test_zero_reranker_weight_reproduces_retrieval_order(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 3,
            "b": 1,
            "c": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
        retrieval_weight=1.0,
        reranker_weight=0.0,
        rrf_k=60,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=3,
    )

    assert [
        result.chunk_id
        for result in results
    ] == [
        "a",
        "b",
        "c",
    ]


# ============================================================
# RERANKER-ONLY WEIGHT
# ============================================================

def test_zero_retrieval_weight_reproduces_ce_order(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 3,
            "b": 1,
            "c": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
        retrieval_weight=0.0,
        reranker_weight=1.0,
        rrf_k=60,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=3,
    )

    assert [
        result.chunk_id
        for result in results
    ] == [
        "b",
        "c",
        "a",
    ]


# ============================================================
# TOP K
# ============================================================

def test_rank_fusion_respects_top_k(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 3,
            "b": 1,
            "c": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=2,
    )

    assert len(results) == 2

    assert results[0].final_rank == 1
    assert results[1].final_rank == 2


def test_top_k_larger_than_candidates_returns_all(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 3,
            "b": 1,
            "c": 2,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=candidates,
        top_k=100,
    )

    assert len(results) == 3


# ============================================================
# EMPTY CANDIDATES
# ============================================================

def test_empty_candidates_returns_empty_list():

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={}
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
    )

    results = fusion_reranker.rerank(
        query="test query",
        candidates=[],
        top_k=5,
    )

    assert results == []


# ============================================================
# QUERY VALIDATION
# ============================================================

def test_empty_query_raises_value_error(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
    )

    with pytest.raises(ValueError):

        fusion_reranker.rerank(
            query="",
            candidates=candidates,
            top_k=5,
        )


def test_whitespace_query_raises_value_error(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
    )

    with pytest.raises(ValueError):

        fusion_reranker.rerank(
            query="    ",
            candidates=candidates,
            top_k=5,
        )


# ============================================================
# TOP K VALIDATION
# ============================================================

def test_zero_top_k_raises_value_error(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
    )

    with pytest.raises(ValueError):

        fusion_reranker.rerank(
            query="test query",
            candidates=candidates,
            top_k=0,
        )


def test_negative_top_k_raises_value_error(
    candidates,
):

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    fusion_reranker = RankFusionReranker(
        reranker=fake_reranker,
    )

    with pytest.raises(ValueError):

        fusion_reranker.rerank(
            query="test query",
            candidates=candidates,
            top_k=-5,
        )


# ============================================================
# CONSTRUCTOR VALIDATION
# ============================================================

def test_negative_retrieval_weight_rejected():

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={}
    )

    with pytest.raises(ValueError):

        RankFusionReranker(
            reranker=fake_reranker,
            retrieval_weight=-0.1,
            reranker_weight=0.5,
        )


def test_negative_reranker_weight_rejected():

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={}
    )

    with pytest.raises(ValueError):

        RankFusionReranker(
            reranker=fake_reranker,
            retrieval_weight=0.5,
            reranker_weight=-0.1,
        )


def test_both_zero_weights_rejected():

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={}
    )

    with pytest.raises(ValueError):

        RankFusionReranker(
            reranker=fake_reranker,
            retrieval_weight=0.0,
            reranker_weight=0.0,
        )


def test_negative_rrf_k_rejected():

    fake_reranker = FakeCrossEncoderReranker(
        ce_ranks={}
    )

    with pytest.raises(ValueError):

        RankFusionReranker(
            reranker=fake_reranker,
            rrf_k=-1,
        )