import pytest
from rag.ingestion.model import Chunk
from rag.retrieval.bm25_retrieval import BM25Retriever


def test_bm25_arabic_tashkeel_and_spelling_invariance():
    # Document has full vocalization/tashkeel and different Alef spelling
    chunk1 = Chunk(
        text="شُرُوطُ تَجْدِيدِ رُخْصَةِ القِيَادَةِ: يَجِبُ إِجْرَاءُ الفَحْصِ الطِّبِّيِّ وَدَفْعُ الرُّسُومِ.",
        source="driver_license.txt",
        file_type="txt",
        chunk_index=0,
        chunking_strategy="structure",
        metadata={"document_id": "doc_driver"},
    )
    chunk2 = Chunk(
        text="إِجْرَاءَاتُ إِصْدَارِ جَوَازِ السَّفَرِ لِلْمَرَّةِ الأُولَى في مكاتب الأحوال المدنية.",
        source="passport.txt",
        file_type="txt",
        chunk_index=1,
        chunking_strategy="structure",
        metadata={"document_id": "doc_passport"},
    )
    chunk3 = Chunk(
        text="معلومات عامة عن حالة الطقس والمناخ في المملكة الأردنية الهاشمية.",
        source="weather.txt",
        file_type="txt",
        chunk_index=2,
        chunking_strategy="structure",
        metadata={"document_id": "doc_weather"},
    )

    retriever = BM25Retriever(chunks=[chunk1, chunk2, chunk3])

    # Query has NO vocalization and uses plain Alef and different Taa Marbuta
    query = "شروط تجديد رخصه القياده والفحص الطبي"
    results = retriever.retrieve(query=query, top_k=2)

    assert len(results) > 0
    assert results[0].chunk_id == chunk1.chunk_id
    assert results[0].score > 0


def test_bm25_arabic_prefix_expansion():
    chunk1 = Chunk(
        text="الوثائق المطلوبة لتقديم المعاملة هي الهوية وصورة شخصية حديثة.",
        source="service.txt",
        file_type="txt",
        chunk_index=0,
        chunking_strategy="structure",
        metadata={"document_id": "doc_service"},
    )
    chunk2 = Chunk(
        text="قائمة المعاملات المتاحة عبر المنصة الإلكترونية الموحدة.",
        source="catalog.txt",
        file_type="txt",
        chunk_index=1,
        chunking_strategy="structure",
        metadata={"document_id": "doc_catalog"},
    )
    chunk3 = Chunk(
        text="دليل المستثمر في المناطق الصناعية الحرة.",
        source="invest.txt",
        file_type="txt",
        chunk_index=2,
        chunking_strategy="structure",
        metadata={"document_id": "doc_invest"},
    )

    retriever = BM25Retriever(chunks=[chunk1, chunk2, chunk3])

    # Query without "ال" should still match "الوثائق" via prefix expansion
    results = retriever.retrieve(query="وثائق مطلوبة", top_k=2)
    assert len(results) > 0
    assert results[0].chunk_id == chunk1.chunk_id
    assert results[0].score > 0
