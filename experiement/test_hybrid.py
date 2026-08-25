from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.retrieval.model import RetrievedChunk


def create_chunk(chunk_id: str, score: float, rank: int):
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=f"Text for {chunk_id}",
        metadata={
            "source": "test.md"
        },
        score=score,
        rank=rank,
    )


class FakeDenseRetriever:

    def __init__(self):
        self.called = False
        self.received_query = None
        self.received_top_k = None

    def retrieve(self, query, top_k=5, filter=None):

        self.called = True
        self.received_query = query
        self.received_top_k = top_k

        return [
            create_chunk("A", 0.9, 1),
            create_chunk("B", 0.8, 2),
        ]


class FakeBM25Retriever:

    def __init__(self):
        self.called = False
        self.received_query = None
        self.received_top_k = None

    def retrieve(self, query, top_k=5, filter=None):

        self.called = True
        self.received_query = query
        self.received_top_k = top_k

        return [
            create_chunk("B", 10.0, 1),
            create_chunk("C", 5.0, 2),
        ]


class FakeFusion:

    def __init__(self):
        self.received_rankings = None

    def fuse(self, rankings):

        self.received_rankings = rankings

        return [
            RetrievedChunk(
                chunk_id="B",
                text="Text for B",
                metadata={
                    "retrieval": {
                        "fusion": "fake"
                    }
                },
                score=0.03,
                rank=1,
            ),
            RetrievedChunk(
                chunk_id="A",
                text="Text for A",
                metadata={
                    "retrieval": {
                        "fusion": "fake"
                    }
                },
                score=0.02,
                rank=2,
            ),
            RetrievedChunk(
                chunk_id="C",
                text="Text for C",
                metadata={
                    "retrieval": {
                        "fusion": "fake"
                    }
                },
                score=0.01,
                rank=3,
            ),
        ]


def test_hybrid_calls_both_retrievers():

    dense = FakeDenseRetriever()
    bm25 = FakeBM25Retriever()
    fusion = FakeFusion()

    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        fusion=fusion,
        candidate_k=5,
    )

    hybrid.retrieve(
        query="test query",
        top_k=3
    )

    assert dense.called
    assert bm25.called


def test_hybrid_passes_results_to_fusion():

    dense = FakeDenseRetriever()
    bm25 = FakeBM25Retriever()
    fusion = FakeFusion()

    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        fusion=fusion,
    )

    hybrid.retrieve(
        query="kubernetes question"
    )

    assert "dense" in fusion.received_rankings
    assert "bm25" in fusion.received_rankings

    assert len(fusion.received_rankings["dense"]) == 2
    assert len(fusion.received_rankings["bm25"]) == 2


def test_hybrid_respects_candidate_k():

    dense = FakeDenseRetriever()
    bm25 = FakeBM25Retriever()
    fusion = FakeFusion()

    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        fusion=fusion,
        candidate_k=20,
    )

    hybrid.retrieve(
        query="test"
    )

    assert dense.received_top_k == 20
    assert bm25.received_top_k == 20


def test_hybrid_returns_top_k_results():

    dense = FakeDenseRetriever()
    bm25 = FakeBM25Retriever()
    fusion = FakeFusion()

    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        fusion=fusion,
    )

    results = hybrid.retrieve(
        query="test",
        top_k=2
    )

    assert len(results) == 2

    assert isinstance(
        results[0],
        RetrievedChunk
    )

    assert results[0].chunk_id == "B"