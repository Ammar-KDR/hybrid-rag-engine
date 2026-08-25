from rag.retrieval.fusion import ReciprocalRankFusion
from rag.retrieval.model import RetrievedChunk


def create_chunk(chunk_id: str, score: float):
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=f"Text for {chunk_id}",
        metadata={
            "source": "test.md"
        },
        score=score,
        rank=0,
    )


def test_rrf_merges_duplicate_chunks():
    dense_results = [
        create_chunk("A", 0.90),
        create_chunk("B", 0.80),
        create_chunk("C", 0.70),
    ]

    bm25_results = [
        create_chunk("B", 12.0),
        create_chunk("D", 8.0),
        create_chunk("A", 5.0),
    ]

    fusion = ReciprocalRankFusion(k=0)

    results = fusion.fuse(
        {
            "dense": dense_results,
            "bm25": bm25_results,
        }
    )

    result_ids = [chunk.chunk_id for chunk in results]

    # B should win because:
    # dense rank 2 + bm25 rank 1
    # A has dense rank 1 + bm25 rank 3
    assert result_ids[0] == "B"
    assert result_ids[1] == "A"

    # No duplicate chunks
    assert len(result_ids) == len(set(result_ids))


def test_rrf_calculates_scores_correctly():
    dense_results = [
        create_chunk("A", 0.90),
    ]

    bm25_results = [
        create_chunk("A", 10.0),
    ]

    fusion = ReciprocalRankFusion(k=0)

    results = fusion.fuse(
        {
            "dense": dense_results,
            "bm25": bm25_results,
        }
    )

    chunk_a = results[0]

    expected_score = (
        1 / (0 + 1) +
        1 / (0 + 1)
    )

    assert chunk_a.score == expected_score


def test_rrf_preserves_retrieval_metadata():
    dense_results = [
        create_chunk("A", 0.85),
    ]

    bm25_results = [
        create_chunk("A", 9.5),
    ]

    fusion = ReciprocalRankFusion(k=60)

    results = fusion.fuse(
        {
            "dense": dense_results,
            "bm25": bm25_results,
        }
    )

    metadata = results[0].metadata["retrieval"]

    assert metadata["fusion"] == "rrf"

    assert "dense" in metadata["sources"]
    assert "bm25" in metadata["sources"]

    assert metadata["sources"]["dense"]["rank"] == 1
    assert metadata["sources"]["bm25"]["rank"] == 1