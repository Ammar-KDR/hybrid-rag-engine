"""Extraction audit and quality tracking for document ingestion.

Tracks per-page extraction statistics, character counts, Arabic linguistic ratio,
detected tables, and explicit status flags ('ok', 'needs_ocr', 'empty', 'warning').
"""

import re
from dataclasses import asdict, dataclass, field


@dataclass
class PageAuditRecord:
    filename: str
    page: int
    method: str  # digital_pdf | docx | ocr | text | manual
    chars: int
    arabic_ratio: float
    tables: int = 0
    status: str = "ok"  # ok | needs_ocr | empty | warning | error
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_arabic_ratio(text: str) -> float:
    """Calculates the ratio of Arabic characters to total non-whitespace characters."""
    if not text:
        return 0.0

    non_ws = re.sub(r"\s+", "", text)
    if not non_ws:
        return 0.0

    # Arabic Unicode range: \u0600-\u06FF, \u0750-\u077F, \u08A0-\u08FF, presentation forms \uFB50-\uFDFF, \uFE70-\uFEFF
    arabic_chars = re.findall(
        r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]",
        non_ws,
    )
    return round(len(arabic_chars) / len(non_ws), 3)


def audit_extracted_page(
    filename: str,
    page_num: int,
    text: str,
    method: str = "digital_pdf",
    tables_count: int = 0,
    has_images: bool = False,
) -> PageAuditRecord:
    """Audits a single page extraction and returns an audit record with quality warnings."""
    clean_text = text.strip() if text else ""
    chars = len(clean_text)
    arabic_ratio = calculate_arabic_ratio(clean_text)
    warnings = []
    status = "ok"

    if chars == 0:
        if has_images:
            status = "needs_ocr"
            warnings.append(
                f"Page {page_num} contains image(s) but no selectable text (scanned page). Requires OCR or manual review."
            )
        else:
            status = "empty"
            warnings.append(f"Page {page_num} is completely empty (no text and no images).")
    elif chars < 30:
        if has_images:
            status = "needs_ocr"
            warnings.append(
                f"Page {page_num} has only {chars} characters despite containing images. Potential scanned document with minimal metadata."
            )
        else:
            status = "warning"
            warnings.append(f"Page {page_num} has low character density ({chars} chars).")

    if chars > 0 and arabic_ratio < 0.15:
        # Document might be primarily English or numeric tables
        warnings.append(f"Low Arabic character ratio ({arabic_ratio:.2f}) on page {page_num}.")

    return PageAuditRecord(
        filename=filename,
        page=page_num,
        method=method,
        chars=chars,
        arabic_ratio=arabic_ratio,
        tables=tables_count,
        status=status,
        warnings=warnings,
    )
