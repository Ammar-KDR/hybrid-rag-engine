import pytest
from rag.generation.service_context_builder import ServiceContextBuilder
from rag.ingestion.service_manifest import ServiceRecord, SourceSpan


def test_service_context_builder_single_service():
    builder = ServiceContextBuilder(max_context_tokens=1000)

    svc = ServiceRecord(
        service_id="svc-id-123",
        document_id="doc-456",
        service_name="إصدار بطاقة شخصية",
        raw_sections=[
            {
                "section_id": "sec-1",
                "service_id": "svc-id-123",
                "section_type": "requirements",
                "heading": "الوثائق المطلوبة",
                "original_text": "صورة شخصية وشهادة ميلاد.",
                "source_span": {"filename": "guide.pdf", "page_number": 1},
            },
            {
                "section_id": "sec-2",
                "service_id": "svc-id-123",
                "section_type": "fees",
                "heading": "الرسوم",
                "original_text": "رسوم الإصدار 2 دينار أردني.",
                "source_span": {"filename": "guide.pdf", "page_number": 1},
            },
            {
                "section_id": "sec-3",
                "service_id": "svc-id-123",
                "section_type": "exceptions",
                "heading": "الاستثناءات",
                "original_text": "يستثنى من الرسوم ذوو الاحتياجات الخاصة بموجب كتاب رسمي.",
                "source_span": {"filename": "guide.pdf", "page_number": 2},
            },
        ],
    )

    ctx = builder.build_from_service(svc, query="ما هي الرسوم والاستثناءات؟")
    assert len(ctx.blocks) == 3
    assert ctx.get_block(1) is not None
    assert ctx.get_block(2) is not None
    assert ctx.get_block(3) is not None
    
    # Verify exception section is preserved
    assert "يستثنى من الرسوم" in ctx.text
    assert "2 دينار" in ctx.text
    assert "المرجع [1]" in ctx.text
    assert "الصفحة: 2" in ctx.text


def test_service_context_builder_comparison():
    builder = ServiceContextBuilder(max_context_tokens=1000)

    svc1 = ServiceRecord(
        service_id="svc-1",
        document_id="doc-1",
        service_name="خدمة جواز السفر",
        raw_sections=[
            {
                "section_id": "sec-1",
                "original_text": "رسوم الجواز 25 دينار.",
                "source_span": {"filename": "p1.pdf", "page_number": 1},
            }
        ],
    )
    svc2 = ServiceRecord(
        service_id="svc-2",
        document_id="doc-2",
        service_name="خدمة الهوية الوطنية",
        raw_sections=[
            {
                "section_id": "sec-2",
                "original_text": "رسوم الهوية 2 دينار.",
                "source_span": {"filename": "p2.pdf", "page_number": 1},
            }
        ],
    )

    ctx = builder.build_comparison([svc1, svc2], query="قارن بين الرسوم")
    assert len(ctx.blocks) == 2
    assert "خدمة جواز السفر" in ctx.text
    assert "خدمة الهوية الوطنية" in ctx.text
    assert "25 دينار" in ctx.text
    assert "2 دينار" in ctx.text
