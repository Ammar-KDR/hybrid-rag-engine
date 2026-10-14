import json
import tempfile
from pathlib import Path
import pytest

from rag.ingestion.model import Document
from rag.ingestion.service_segmenter import (
    ServiceSegmenter,
    is_service_boundary_line,
    service_records_to_chunks,
)
from rag.ingestion.service_manifest import (
    classify_section_type,
    generate_service_aliases,
)


def test_service_boundary_line_detection():
    # Positive service anchors
    is_svc, title = is_service_boundary_line("اسم الخدمة: إصدار بطاقة شخصية جديدة")
    assert is_svc is True
    assert title == "إصدار بطاقة شخصية جديدة"

    is_svc, title = is_service_boundary_line("خدمة تجديد جواز السفر الإلكتروني")
    assert is_svc is True
    assert "تجديد جواز السفر الإلكتروني" in title

    is_svc, title = is_service_boundary_line("# دليل خدمة الحصول على عدم محكومية")
    assert is_svc is True

    # Negative: section headings MUST NOT be treated as new service boundaries
    is_svc, _ = is_service_boundary_line("الرسوم المقررة:")
    assert is_svc is False

    is_svc, _ = is_service_boundary_line("الشروط الواجب توفرها:")
    assert is_svc is False

    is_svc, _ = is_service_boundary_line("الوثائق والمستندات المطلوبة:")
    assert is_svc is False


def test_classify_section_types():
    assert classify_section_type("رسوم الخدمة") == "fees"
    assert classify_section_type("المستندات والوثائق المطلوبة") == "requirements"
    assert classify_section_type("شروط الحصول على الخدمة") == "eligibility"
    assert classify_section_type("إجراءات وخطوات التنفيذ") == "steps"
    assert classify_section_type("الوقت المستغرق لإنجاز المعاملة") == "processing_time"
    assert classify_section_type("قنوات تقديم الخدمة") == "channels"
    assert classify_section_type("ملاحظات واستثناءات") == "exceptions"


def test_single_service_file_segmentation():
    segmenter = ServiceSegmenter()
    doc = Document(
        text="""اسم الخدمة: إصدار شهادة ولادة
الشروط:
أن يكون المولود قد تم تسجيله رسمياً.
الرسوم:
رسوم الإصدار 2 دينار أردني.""",
        source="birth_certificate.pdf",
        file_type="pdf",
        metadata={"page_number": 1, "page_count": 1, "extraction_method": "digital_pdf"},
    )
    
    services = segmenter.segment([doc], document_id="doc-abc-123", filename="birth_certificate.pdf")
    assert len(services) == 1
    svc = services[0]
    assert svc.service_name == "إصدار شهادة ولادة"
    assert svc.document_id == "doc-abc-123"
    assert len(svc.raw_sections) >= 2
    
    section_types = [sec["section_type"] for sec in svc.raw_sections]
    assert "eligibility" in section_types
    assert "fees" in section_types


def test_multi_service_combined_document_segmentation():
    segmenter = ServiceSegmenter()
    # A single PDF file with 2 services on different pages
    doc_p1 = Document(
        text="""اسم الخدمة: إصدار بدل فاقد للهوية
الرسوم:
50 دينار للمرة الثانية.""",
        source="combined_guide.pdf",
        file_type="pdf",
        metadata={"page_number": 1, "page_count": 2, "extraction_method": "digital_pdf"},
    )
    doc_p2 = Document(
        text="""اسم الخدمة: تجديد جواز السفر
الرسوم:
25 دينار للبالغين.""",
        source="combined_guide.pdf",
        file_type="pdf",
        metadata={"page_number": 2, "page_count": 2, "extraction_method": "digital_pdf"},
    )

    services = segmenter.segment([doc_p1, doc_p2], document_id="doc-combined-999", filename="combined_guide.pdf")
    assert len(services) == 2
    
    svc1, svc2 = services[0], services[1]
    assert svc1.service_name == "إصدار بدل فاقد للهوية"
    assert svc2.service_name == "تجديد جواز السفر"
    
    # Must have distinct, stable service_ids despite sharing the same document_id!
    assert svc1.document_id == svc2.document_id == "doc-combined-999"
    assert svc1.service_id != svc2.service_id


def test_service_records_to_chunks_parity():
    segmenter = ServiceSegmenter()
    doc = Document(
        text="""اسم الخدمة: فحص اللياقة الصحية
الرسوم:
15 دينار.""",
        source="medical.pdf",
        file_type="pdf",
        metadata={"page_number": 1, "page_count": 1, "extraction_method": "digital_pdf"},
    )
    services = segmenter.segment([doc], document_id="doc-med-777", filename="medical.pdf")
    chunks = service_records_to_chunks(services)
    
    assert len(chunks) >= 1
    chk = chunks[0]
    
    # Check 100% metadata parity
    assert chk.metadata["document_id"] == "doc-med-777"
    assert chk.metadata["service_id"] == services[0].service_id
    assert chk.metadata["service_name"] == "فحص اللياقة الصحية"
    assert "section_type" in chk.metadata
    assert chk.metadata["page_number"] == 1
    assert chk.metadata["extraction_method"] == "digital_pdf"
    assert chk.chunk_id is not None
