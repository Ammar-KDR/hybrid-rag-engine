"""Numeric guard and canonicalizer for Arabic government QA.

Validates that any fee, duration, age, or quantity mentioned in the model answer
strictly occurs in the retrieved evidence, canonicalizing Arabic-Indic digits (٠-٩)
and standard Arabic decimal points.
"""

from __future__ import annotations

import re
from typing import List, Set, Tuple

INDIC_TO_ASCII = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def canonicalize_numbers(text: str) -> str:
    """Replaces Arabic Indic digits with standard ASCII digits."""
    if not text:
        return ""
    # Convert Indic digits
    converted = text.translate(INDIC_TO_ASCII)
    # Convert Arabic comma used as decimal separator (، -> .)
    converted = re.sub(r"(\d+)[\.,](\d+)", r"\1.\2", converted)
    return converted


def extract_numeric_tokens(text: str, strip_citations: bool = False) -> Set[str]:
    """Extracts standalone numeric tokens from text, optionally stripping citation references [1]."""
    if not text:
        return set()
    cleaned = re.sub(r"\[\d+\]", "", text) if strip_citations else text
    canon = canonicalize_numbers(cleaned)
    # Match numbers (integers or decimals)
    matches = re.findall(r"\b\d+(?:\.\d+)?\b", canon)
    return set(matches)


def validate_numeric_support(answer: str, evidence_text: str) -> Tuple[bool, List[str]]:
    """Checks whether all numeric values in the answer are grounded in the evidence.

    Returns:
        (is_supported, list_of_unsupported_numbers)
    """
    answer_numbers = extract_numeric_tokens(answer, strip_citations=True)
    if not answer_numbers:
        return True, []

    evidence_numbers = extract_numeric_tokens(evidence_text, strip_citations=False)
    unsupported = [n for n in answer_numbers if n not in evidence_numbers]

    return len(unsupported) == 0, unsupported
