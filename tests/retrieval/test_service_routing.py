import pytest
from types import SimpleNamespace

from rag.ingestion.service_manifest import ServiceRecord
from rag.retrieval.model import RetrievalFilter, RetrievedChunk
from rag.retrieval.service_router import ServiceRouter, RouteResult
from rag.retrieval.bm25_retrieval import BM25Retriever


def test_service_router_exact_title():
    svc1 = ServiceRecord(
        service_id="svc-id-card",
        document_id="doc-1",
        service_name="إصدار بطاقة شخصية جديدة",
        aliases=["بطاقة شخصية", "الهوية الوطنية"],
    )
    svc2 = ServiceRecord(
        service_id="svc-passport",
        document_id="doc-2",
        service_name="تجديد جواز السفر الأردني",
        aliases=["جواز السفر", "تجديد الجواز"],
    )

    router = ServiceRouter([svc1, svc2])

    res = router.route("كم رسوم إصدار بطاقة شخصية جديدة للمواطن؟")
    assert res.primary_service is not None
    assert res.primary_service.service_id == "svc-id-card"
    assert res.confidence >= 0.90
    assert res.routing_reason in ("exact_title", "alias_match", "token_overlap")


def test_service_router_alias():
    svc1 = ServiceRecord(
        service_id="svc-lost",
        document_id="doc-1",
        service_name="إصدار بدل فاقد للبطاقة الشخصية",
        aliases=["بدل فاقد", "فاقد الهوية"],
    )
    svc2 = ServiceRecord(
        service_id="svc-passport",
        document_id="doc-2",
        service_name="تجديد جواز السفر",
        aliases=["جواز السفر"],
    )

    router = ServiceRouter([svc1, svc2])

    res = router.route("ما الأوراق المطلوبة لطلب بدل فاقد؟")
    assert res.primary_service is not None
    assert res.primary_service.service_id == "svc-lost"
    assert res.confidence >= 0.90


def test_service_router_follow_up_pronoun():
    svc = ServiceRecord(
        service_id="svc-passport-1",
        document_id="doc-1",
        service_name="تجديد جواز السفر",
        aliases=["جواز السفر"],
    )
    router = ServiceRouter([svc])

    history = [
        {"question": "ما هي شروط تجديد جواز السفر؟", "service_id": "svc-passport-1"}
    ]

    res = router.route("كم رسومها؟", history=history)
    assert res.primary_service is not None
    assert res.primary_service.service_id == "svc-passport-1"
    assert res.routing_reason == "follow_up_context"


def test_service_router_comparison():
    svc1 = ServiceRecord(
        service_id="svc-passport",
        document_id="doc-1",
        service_name="تجديد جواز السفر",
        aliases=["جواز السفر"],
    )
    svc2 = ServiceRecord(
        service_id="svc-id-card",
        document_id="doc-2",
        service_name="إصدار بطاقة شخصية جديدة",
        aliases=["بطاقة شخصية"],
    )
    router = ServiceRouter([svc1, svc2])

    res = router.route("ما الفرق بين تجديد جواز السفر وإصدار بطاقة شخصية جديدة؟")
    assert len(res.routed_services) == 2
    assert "svc-passport" in res.service_ids
    assert "svc-id-card" in res.service_ids


def test_bm25_retriever_service_scoped_filter():
    # Two chunks with identical text "الرسوم المقررة" but different service_ids
    chk1 = SimpleNamespace(
        chunk_id="chk-1",
        text="الرسوم المقررة لإصدار الهوية هي 2 دينار",
        source="doc1.pdf",
        file_type="pdf",
        chunk_index=0,
        chunking_strategy="arabic_structure",
        metadata={"document_id": "doc-1", "service_id": "svc-id-card"},
    )
    chk2 = SimpleNamespace(
        chunk_id="chk-2",
        text="الرسوم المقررة لتجديد الجواز هي 25 دينار",
        source="doc2.pdf",
        file_type="pdf",
        chunk_index=0,
        chunking_strategy="arabic_structure",
        metadata={"document_id": "doc-2", "service_id": "svc-passport"},
    )

    retriever = BM25Retriever([chk1, chk2])

    # 1. Without filter: both match
    all_res = retriever.retrieve("الرسوم المقررة", top_k=5)
    assert len(all_res) == 2

    # 2. Filter scoped specifically to svc-id-card
    filt = RetrievalFilter(service_ids=("svc-id-card",))
    scoped_res = retriever.retrieve("الرسوم المقررة", top_k=5, filter=filt)
    
    assert len(scoped_res) == 1
    assert scoped_res[0].metadata["service_id"] == "svc-id-card"
    assert "2 دينار" in scoped_res[0].text
    assert "25 دينار" not in scoped_res[0].text
