from rag.retrieval.bm25_retrieval import BM25Retriever


def test_bm25_init_with_empty_list():
    retriever = BM25Retriever([])
    assert retriever.chunks == []
    assert retriever.index is None
    results = retriever.retrieve("hello world")
    assert results == []


def test_bm25_init_with_none():
    retriever = BM25Retriever(None)
    assert retriever.chunks == []
    assert retriever.index is None
    results = retriever.retrieve("test query")
    assert results == []
