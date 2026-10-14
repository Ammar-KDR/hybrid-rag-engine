import pytest
from rag.verification.numeric_guard import (
    canonicalize_numbers,
    extract_numeric_tokens,
    validate_numeric_support,
)


def test_canonicalize_numbers():
    arabic_indic = "الرسوم هي ٥٠ ديناراً وفي المرة الأولى ٢.٥ دينار"
    canon = canonicalize_numbers(arabic_indic)
    assert "50" in canon
    assert "2.5" in canon


def test_extract_numeric_tokens():
    text = "الرسوم للمرة الأولى 10 دنانير، والمرة الثانية ٥٠ ديناراً بنسبة 15% خلال 3 أيام"
    tokens = extract_numeric_tokens(text)
    assert "10" in tokens
    assert "50" in tokens
    assert "15" in tokens
    assert "3" in tokens


def test_validate_numeric_support_positive():
    evidence = "رسوم إصدار بدل فاقد للمرة الثانية 50 دينار وللمرة الأولى 10 دنانير."
    answer = "تبلغ رسوم بدل فاقد للمرة الثانية 50 ديناراً [1]."
    
    is_valid, unsupported = validate_numeric_support(answer, evidence)
    assert is_valid is True
    assert len(unsupported) == 0


def test_validate_numeric_support_indic_positive():
    evidence = "رسوم إصدار بدل فاقد للمرة الثانية 50 دينار."
    answer = "تبلغ الرسوم ٥٠ ديناراً للمرة الثانية [1]."
    
    is_valid, unsupported = validate_numeric_support(answer, evidence)
    assert is_valid is True
    assert len(unsupported) == 0


def test_validate_numeric_support_negative_hallucination():
    evidence = "رسوم تجديد الجواز 25 ديناراً."
    # Model hallucinated 100 JOD
    answer = "تبلغ الرسوم 100 دينار للمواطنين [1]."
    
    is_valid, unsupported = validate_numeric_support(answer, evidence)
    assert is_valid is False
    assert "100" in unsupported
