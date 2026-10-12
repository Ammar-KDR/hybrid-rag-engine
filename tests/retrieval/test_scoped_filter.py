from unittest.mock import MagicMock
from rag.retrieval.model import RetrievalFilter, RetrievedChunk
from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.ingestion.model import Chunk


def _make_dummy_chunk(chunk_id: str, text: str, doc_id: str, filename: str) -> Chunk:
    c = Chunk(
        text=text,
        source=f"data/raw/{filename}",
        file_type="md",
        chunk_index=0,
        chunking_strategy="structure",
        metadata={"document_id": doc_id, "filename": filename},
    )
    c.chunk_id = chunk_id
    return c


def test_bm25_scoped_filter():
    chunk1 = _make_dummy_chunk("c1", "docker restart policy always", "doc_docker", "docker.md")
    chunk2 = _make_dummy_chunk("c2", "kubernetes restart policy never", "doc_k8s", "k8s.md")
    chunk3 = _make_dummy_chunk("c3", "database timeout policy", "doc_db", "db.md")

    retriever = BM25Retriever([chunk1, chunk2, chunk3])

    # 1. Unfiltered query matches all 3 chunks (all contain 'restart' or 'policy')
    all_res = retriever.retrieve("restart policy", top_k=5)
    assert len(all_res) == 3

    # 2. Filter strictly for doc_docker
    docker_filter = RetrievalFilter(document_ids=("doc_docker",))
    docker_res = retriever.retrieve("restart policy", top_k=5, filter=docker_filter)
    assert len(docker_res) == 1
    assert docker_res[0].chunk_id == "c1"
    assert docker_res[0].metadata["document_id"] == "doc_docker"

    # 3. Filter strictly for doc_k8s
    k8s_filter = RetrievalFilter(document_ids=("doc_k8s",))
    k8s_res = retriever.retrieve("restart policy", top_k=5, filter=k8s_filter)
    assert len(k8s_res) == 1
    assert k8s_res[0].chunk_id == "c2"
    assert k8s_res[0].metadata["document_id"] == "doc_k8s"

    # 4. Filter for non-existent doc returns empty
    empty_res = retriever.retrieve("restart policy", top_k=5, filter=RetrievalFilter(document_ids=("doc_missing",)))
    assert empty_res == []


def test_dense_retriever_filter_translation():
    mock_embed = MagicMock()
    mock_embed.embed_text.return_value = [0.1, 0.2, 0.3]

    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = []

    retriever = DenseRetriever(
        embedding_service=mock_embed,
        vector_store=mock_vector_store,
        collection_name="test_col",
    )

    filt = RetrievalFilter(document_ids=("doc_alpha", "doc_beta"))
    retriever.retrieve("my test query", top_k=3, filter=filt)

    # Verify vector_store.search was called with a Qdrant Filter containing document_id match
    mock_vector_store.search.assert_called_once()
    args, kwargs = mock_vector_store.search.call_args
    passed_filter = args[3]
    assert passed_filter is not None
    assert len(passed_filter.must) == 1
    assert passed_filter.must[0].key == "document_id"
    assert passed_filter.must[0].match.any == ["doc_alpha", "doc_beta"]


def test_hybrid_retriever_forwards_filter():
    mock_dense = MagicMock()
    mock_dense.retrieve.return_value = []

    mock_bm25 = MagicMock()
    mock_bm25.retrieve.return_value = []

    mock_fusion = MagicMock()
    mock_fusion.fuse.return_value = []

    hybrid = HybridRetriever(
        dense_retriever=mock_dense,
        bm25_retriever=mock_bm25,
        fusion=mock_fusion,
        candidate_k=10,
    )

    filt = RetrievalFilter(document_ids=("doc_target",))
    hybrid.retrieve("check filters", top_k=5, filter=filt)

    mock_dense.retrieve.assert_called_once_with(query="check filters", top_k=10, filter=filt)
    mock_bm25.retrieve.assert_called_once_with(query="check filters", top_k=10, filter=filt)
