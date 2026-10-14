import pytest
from pathlib import Path
from unittest.mock import MagicMock

from rag.config import settings
from rag.ingestion.loader import load_document
from rag.ingestion.service_segmenter import ServiceSegmenter
from rag.retrieval.service_router import ServiceRouter
from rag.verification.numeric_guard import canonicalize_numbers, extract_numeric_tokens, validate_numeric_support


@pytest.fixture
def fixtures_dir():
    return Path(__file__).resolve().parent.parent.parent / "data" / "hackathon" / "fixtures"


def test_separate_docs_segmentation(fixtures_dir):
    separate_dir = fixtures_dir / "separate_docs"
    if not separate_dir.exists():
        pytest.skip("Separate fixtures not generated yet")

    segmenter = ServiceSegmenter()
    all_services = []
    pdf_files = list(separate_dir.glob("*.pdf"))
    assert len(pdf_files) == 10

    for pdf in pdf_files:
        docs = load_document(pdf)
        assert len(docs) >= 1
        services = segmenter.segment(docs, f"doc_{pdf.stem}", pdf.name)
        assert len(services) >= 1
        all_services.extend(services)

    # 10 separate documents should produce at least 10 services
    assert len(all_services) >= 10
    service_names = [s.service_name for s in all_services]
    # Check that key services exist
    assert any("البطاقة الشخصية" in name for name in service_names)
    assert any("جواز السفر" in name for name in service_names)
    assert any("ترخيص" in name and "المركبات" in name for name in service_names)


def test_combined_doc_segmentation(fixtures_dir):
    combined_pdf = fixtures_dir / "combined_docs" / "دليل_الخدمات_الحكومية_الموحد_2026.pdf"
    if not combined_pdf.exists():
        pytest.skip("Combined fixture not generated yet")

    segmenter = ServiceSegmenter()
    docs = load_document(combined_pdf)
    assert len(docs) >= 5

    services = segmenter.segment(docs, "combined_doc_001", combined_pdf.name)
    # The combined PDF contains 10 services under ONE document_id
    assert len(services) >= 8  # Successfully demarcated across page boundaries
    for svc in services:
        assert svc.document_id == "combined_doc_001"
        assert len(svc.sections) >= 1


def test_service_router_follow_up_with_chat_history(fixtures_dir):
    separate_dir = fixtures_dir / "separate_docs"
    if not separate_dir.exists():
        pytest.skip("Separate fixtures not generated yet")

    segmenter = ServiceSegmenter()
    all_services = []
    for pdf in sorted(separate_dir.glob("*.pdf"))[:3]:
        docs = load_document(pdf)
        all_services.extend(segmenter.segment(docs, f"doc_{pdf.stem}", pdf.name))

    router = ServiceRouter(all_services)

    history = [
        {"role": "user", "content": "ما هي رسوم إصدار جواز السفر؟"},
        {"role": "assistant", "content": "تبلغ رسوم جواز السفر 50 ديناراً."},
    ]

    res = router.route("وكم رسوم المستعجل منه؟", history=history)
    assert res.primary_service is not None
    assert "جواز" in res.primary_service.service_name
    assert res.routing_reason == "follow_up_context"


def test_service_router_comparison_resolution(fixtures_dir):
    separate_dir = fixtures_dir / "separate_docs"
    if not separate_dir.exists():
        pytest.skip("Separate fixtures not generated yet")

    segmenter = ServiceSegmenter()
    all_services = []
    for pdf in sorted(separate_dir.glob("*.pdf"))[:4]:
        docs = load_document(pdf)
        all_services.extend(segmenter.segment(docs, f"doc_{pdf.stem}", pdf.name))

    router = ServiceRouter(all_services)
    res = router.route("قارن بين رسوم بدل الفاقد بين البطاقة الشخصية وجواز السفر")
    assert len(res.routed_services) >= 2
    routed_names = [s.service_name for s in res.routed_services]
    assert any("البطاقة" in n for n in routed_names)
    assert any("جواز" in n for n in routed_names)


def test_indic_arabic_numbers_validation():
    # Model generates Arabic-Indic digits ٥٠ and 25
    answer = "رسم بدل الفاقد للمرة الأولى هو 25 ديناراً وللمرة الثانية ٥٠ ديناراً [1]."
    evidence = "استيفاء رسم بدل فاقد للمرة الأولى بقيمة 25 ديناراً وللمرة الثانية 50 ديناراً."

    supported, unsupported = validate_numeric_support(answer, evidence)
    assert supported is True
    assert unsupported == []

    # If model hallucinates an unsupported fee
    unsupported_answer = "رسم بدل الفاقد هو ٧٥ ديناراً."
    supported, unsupported = validate_numeric_support(unsupported_answer, evidence)
    assert supported is False
    assert "75" in unsupported
