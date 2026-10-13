import pytest
from rag.ingestion.model import Document
from rag.chunking.arabic_chunker import ArabicGovernmentChunker


def test_arabic_chunker_empty_document():
    chunker = ArabicGovernmentChunker()
    doc = Document(text="", source="doc.txt", file_type="txt")
    chunks = chunker.chunk(doc)
    assert chunks == []


def test_arabic_chunker_structure_and_context_injection():
    text = """# دليل خدمة إصدار جواز السفر الأردني

شروط الحصول على الخدمة:
1- أن يكون مقدم الطلب أردني الجنسية ويحمل رقماً وطنياً.
2- أن لا يقل العمر عن 16 عاماً أو بحضور ولي الأمر.

الوثائق والمستندات المطلوبة:
1- بطاقة الأحوال المدنية الذكية سارية المفعول.
2- صورتان شخصيتان حديثتان خلفية بيضاء.
3- دفتر العائلة للمتزوجين.

الرسوم المقررة:
تستوفى رسوم بقيمة 50 ديناراً للجواز العادي، و100 دينار للمعاملة المستعجلة.
"""
    doc = Document(text=text, source="passport_guide.txt", file_type="txt")
    chunker = ArabicGovernmentChunker(max_chunk_chars=1200, inject_heading_context=True)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 3

    # Verify context injection
    # Chunks should contain breadcrumbs indicating the section
    docs_chunk = next(c for c in chunks if "بطاقة الأحوال" in c.text)
    assert "[دليل خدمة إصدار جواز السفر الأردني > الوثائق والمستندات المطلوبة]" in docs_chunk.text
    assert docs_chunk.metadata["heading"] == "الوثائق والمستندات المطلوبة"
    assert docs_chunk.chunking_strategy == "arabic_government_structure"

    fees_chunk = next(c for c in chunks if "50 ديناراً" in c.text)
    assert "[دليل خدمة إصدار جواز السفر الأردني > الرسوم المقررة]" in fees_chunk.text
    assert fees_chunk.metadata["heading"] == "الرسوم المقررة"


def test_arabic_chunker_legal_clauses():
    text = """المادة (1):
يسمى هذا النظام نظام رخص المهن في أمانة عمان الكبرى لسنة 2026.

المادة (2):
تستوفى الرسوم السنوية المقررة عن المهن المحددة في الجدول رقم (1) الملحق بهذا النظام.
"""
    doc = Document(text=text, source="law.txt", file_type="txt")
    chunker = ArabicGovernmentChunker()
    chunks = chunker.chunk(doc)

    assert len(chunks) == 2
    assert "المادة (1)" in chunks[0].text
    assert "المادة (2)" in chunks[1].text
