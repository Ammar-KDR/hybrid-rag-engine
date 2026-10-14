"""Table serialization utility for structured, loss-preserving RAG ingestion.

Converts detected tables into self-contained row-level statements and clean Markdown tables,
guaranteeing that fees, SLAs, and conditions remain strictly bound to their correct rows.
Filters out whole-page service card layouts to prevent cell scrambling and duplication.
"""

from typing import Any
import re
from rag.nlp.arabic import fix_visual_arabic


MUNICIPAL_CANONICAL_HEADERS = [
    (re.compile(r".*(?:قىيلة|موسرلا|رسب|الرسوئ).*"), "قيمة الرسوم"),
    (re.compile(r".*(?:المعياري|المستغرق|النن مخ|يرانعيما).*"), "الزمن المعياري لتقديم الخدمة"),
    (re.compile(r".*(?:طورش).*"), "شروط تقديم الخدمة"),
    (re.compile(r".*(?:ال ثائق|الو ي ة|قئاثولا).*"), "الوثائق المطلوبة"),
    (re.compile(r".*(?:حارم|لحام).*"), "مراحل تقديم الخدمة"),
    (re.compile(r".*(?:قن ال|تاونق).*"), "قنوات تقديم الخدمة"),
    (re.compile(r".*(?:أوقال|تاقوم).*"), "أوقات تقديم الخدمة"),
    (re.compile(r".*(?:مخمج|جرخم).*"), "مخرج الخدمة"),
    (re.compile(r".*(?:اصىللية|ةي لص|ةيرلاص).*"), "مدة صلاحية الوثيقة"),
    (re.compile(r".*(?:الدنع|عندلا|فدلا).*"), "آلية الدفع"),
    (re.compile(r".*(?:ةمدخلا مسا).*"), "اسم الخدمة"),
    (re.compile(r".*(?:ةمدخلا فصو).*"), "وصف الخدمة"),
    (re.compile(r".*(?:ةهج رادص).*"), "جهة إصدار الوثيقة"),
    (re.compile(r".*(?:لكش ةقيثولا|شنل).*"), "شكل الوثيقة"),
    (re.compile(r".*(?:كيرشلا|اكش لا).*"), "الشريك ودوره"),
]


def clean_table_header(header_text: str) -> str:
    """Cleans reversed/distorted header text and maps to canonical standard terminology."""
    cleaned = fix_visual_arabic(str(header_text).strip())
    cleaned = re.sub(r"ـ+", "", cleaned)
    cleaned = re.sub(r"([\u0600-\u06FF])\1{2,}", r"\1", cleaned).strip()
    if not cleaned:
        return ""
    # If already standard clean Arabic, preserve as-is
    if cleaned in ("الرسوم", "قيمة الرسوم", "الخدمة", "اسم الخدمة", "الحالة", "الوثائق المطلوبة"):
        return cleaned
    for pattern, canonical in MUNICIPAL_CANONICAL_HEADERS:
        if pattern.match(cleaned):
            return canonical
    return cleaned


def clean_table_cell(cell_value: Any) -> str:
    """Cleans a table cell line-by-line to preserve multi-line logical ordering."""
    if cell_value is None:
        return ""
    raw = str(cell_value).strip()
    if not raw:
        return ""
    # Process line-by-line so multi-line text does not invert paragraph order
    fixed_lines = [
        fix_visual_arabic(re.sub(r"ـ+", "", line).strip())
        for line in raw.splitlines()
        if line.strip()
    ]
    joined = " | ".join(fixed_lines)
    # Collapse 3+ repeated Arabic letters
    return re.sub(r"([\u0600-\u06FF])\1{2,}", r"\1", joined).strip()


def serialize_table_to_records(
    headers: list[str],
    rows: list[list[str]],
    table_index: int = 1,
) -> str:
    """Serializes a 2D table into self-contained key-value row representations.

    Example output:
    [جدول 1]
    الخدمة: إصدار بدل فاقد | المرة الأولى: 10 دنانير | المرة الثانية: 50 دينار
    """
    clean_headers = [clean_table_header(h) if h else f"عمود {i+1}" for i, h in enumerate(headers)]

    # Determine maximum number of columns across headers and all rows
    max_cols = max(len(clean_headers), max((len(r) for r in rows), default=0))
    while len(clean_headers) < max_cols:
        clean_headers.append(f"عمود {len(clean_headers) + 1}")

    serialized_lines = [f"[جدول {table_index}]"]

    # 1. Self-contained key-value rows (vital for LLM fee/condition binding)
    for row in rows:
        row_parts = []
        for i, cell in enumerate(row):
            h = clean_headers[i] if i < len(clean_headers) else f"عمود {i+1}"
            c_text = clean_table_cell(cell)
            if c_text:
                if h and not h.startswith("عمود"):
                    row_parts.append(f"{h}: {c_text}")
                else:
                    row_parts.append(c_text)
        if row_parts:
            serialized_lines.append(" | ".join(row_parts))

    # 2. Markdown table representation for tabular readability
    if rows and clean_headers:
        serialized_lines.append("")
        serialized_lines.append("| " + " | ".join(clean_headers) + " |")
        serialized_lines.append("| " + " | ".join(["---"] * len(clean_headers)) + " |")
        for row in rows:
            cells = [clean_table_cell(c) for c in row]
            while len(cells) < len(clean_headers):
                cells.append("")
            serialized_lines.append("| " + " | ".join(cells[:len(clean_headers)]) + " |")

    return "\n".join(serialized_lines)


def extract_and_serialize_pymupdf_tables(page: Any, page_num: int) -> tuple[str, int]:
    """Attempts native table extraction on a PyMuPDF page.

    Filters out full-page service card form outlines (which duplicate and scramble
    the cleanly extracted page text) while preserving true tabular data (fee schedules, partner matrices).

    Returns:
        (serialized_tables_text, count_of_tables_found)
    """
    if not hasattr(page, "find_tables"):
        return "", 0

    try:
        tabs = page.find_tables()
        if not tabs or not getattr(tabs, "tables", None):
            return "", 0

        serialized_blocks = []
        table_count = 0
        for t_idx, tab in enumerate(tabs.tables, start=1):
            extracted = tab.extract()
            if not extracted or len(extracted) < 1:
                continue

            # Check if this "table" is actually the entire service card page form layout
            first_row_str = " ".join(str(c or "") for c in extracted[0])
            first_row_cleaned = fix_visual_arabic(first_row_str)
            if "بطاقة الخدمة" in first_row_cleaned or "ةمدخلا ةقاطب" in first_row_str:
                # This is the outer bounding card form, not an embedded table
                continue

            # Real table: extract header and data rows
            headers = [str(c) if c is not None else "" for c in extracted[0]]
            data_rows = extracted[1:] if len(extracted) > 1 else []

            # If headers are empty but rows exist, treat first row as data
            if not any(headers) and data_rows:
                headers = [f"عمود {i+1}" for i in range(len(extracted[0]))]
                data_rows = extracted

            table_text = serialize_table_to_records(headers, data_rows, table_index=t_idx)
            serialized_blocks.append(table_text)
            table_count += 1

        return "\n\n".join(serialized_blocks), table_count
    except Exception:
        return "", 0
