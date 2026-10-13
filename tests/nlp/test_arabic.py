import pytest
from rag.nlp.arabic import (
    normalize_arabic,
    remove_tashkeel,
    remove_tatweel,
    tokenize_arabic,
    is_arabic_text,
    is_arabic_heading,
    split_arabic_sentences,
)


def test_remove_tashkeel_and_tatweel():
    vocalized = "شُرُوطُ التَّسْجِيلِ"
    assert remove_tashkeel(vocalized) == "شروط التسجيل"
    
    with_tatweel = "خـــــدمة"
    assert remove_tatweel(with_tatweel) == "خدمة"


def test_normalize_arabic():
    # Alef variants
    assert normalize_arabic("إجراءات وأوراق") == "اجراءات واوراق"
    assert normalize_arabic("تأكيد") == "تاكيد"
    # Taa Marbuta & Alef Maqsura
    assert normalize_arabic("الخدمة المدنية على مستوى") == "الخدمه المدنيه علي مستوي"


def test_tokenize_arabic_prefix_expansion():
    tokens = tokenize_arabic("شروط الخدمة والرسوم")
    # Should include base and stripped prefix
    assert "الخدمه" in tokens
    assert "خدمه" in tokens
    assert "والرسوم" in tokens
    assert "رسوم" in tokens


def test_is_arabic_heading():
    # Legal clauses
    is_head, title, lvl = is_arabic_heading("المادة (12): الرسوم المقررة")
    assert is_head is True
    assert lvl == 2

    # Government service sections
    is_head, title, lvl = is_arabic_heading("شروط الحصول على الخدمة:")
    assert is_head is True
    assert lvl == 2

    is_head, title, lvl = is_arabic_heading("الوثائق والمستندات المطلوبة")
    assert is_head is True

    # Regular body line (not a heading)
    is_head, title, lvl = is_arabic_heading("يجب على المواطن إحضار بطاقة الأحوال المدنية سارية المفعول ودفع المبلغ المستحق في المركز.")
    assert is_head is False


def test_split_arabic_sentences():
    text = "يجب إحضار الهوية الشخصية، وصورة مصدقة عن شهادة الميلاد. كما يشترط دفع الرسوم المقررة وقدرها عشرون ديناراً."
    sentences = split_arabic_sentences(text)
    assert len(sentences) >= 2
    assert any("الهوية" in s for s in sentences)
    assert any("الرسوم" in s for s in sentences)
