"""Table serialization utility for structured, loss-preserving RAG ingestion.

Converts detected tables into self-contained row-level statements and clean Markdown tables,
guaranteeing that fees, SLAs, and conditions remain strictly bound to their correct rows.
"""

from typing import Any


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
    clean_headers = [str(h).strip().replace("\n", " ") if h else f"عمود {i+1}" for i, h in enumerate(headers)]
    
    serialized_lines = [f"[جدول {table_index}]"]
    
    # 1. Self-contained key-value rows (vital for LLM fee/condition binding)
    for row in rows:
        row_parts = []
        for h, cell in zip(clean_headers, row):
            c_text = str(cell).strip().replace("\n", " ") if cell is not None else ""
            if c_text:
                if h:
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
            cells = [str(cell).strip().replace("\n", " ") if cell is not None else "" for cell in row]
            # Pad if row is shorter than headers
            while len(cells) < len(clean_headers):
                cells.append("")
            serialized_lines.append("| " + " | ".join(cells[:len(clean_headers)]) + " |")

    return "\n".join(serialized_lines)


def extract_and_serialize_pymupdf_tables(page: Any, page_num: int) -> tuple[str, int]:
    """Attempts native table extraction on a PyMuPDF page.

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
