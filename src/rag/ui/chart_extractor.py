"""Chart extraction and automatic table-to-chart synthesizer for RAG UI.

Extracts explicit ```chart ... ``` JSON code blocks and automatically synthesizes
interactive comparison charts (fees, SLA/durations) from Markdown comparison tables.
"""

import json
import re
from typing import Any


ARABIC_WORD_NUMBERS: dict[str, float] = {
    "يومان": 2.0,
    "يومين": 2.0,
    "يومي": 2.0,
    "ساعتان": 2.0,
    "ساعتين": 2.0,
    "يوم": 1.0,
    "ساعة": 1.0,
    "واحد": 1.0,
    "واحدة": 1.0,
    "اثنان": 2.0,
    "اثنين": 2.0,
    "ثلاثة": 3.0,
    "ثلاث": 3.0,
    "أربعة": 4.0,
    "أربع": 4.0,
    "خمسة": 5.0,
    "خمس": 5.0,
    "ستة": 6.0,
    "ست": 6.0,
    "سبعة": 7.0,
    "سبع": 7.0,
    "ثمانية": 8.0,
    "ثمان": 8.0,
    "تسعة": 9.0,
    "تسع": 9.0,
    "عشرة": 10.0,
    "عشر": 10.0,
    "عشرون": 20.0,
    "عشرين": 20.0,
    "ثلاثون": 30.0,
    "ثلاثين": 30.0,
    "أربعون": 40.0,
    "أربعين": 40.0,
    "خمسون": 50.0,
    "خمسين": 50.0,
    "ستون": 60.0,
    "ستين": 60.0,
    "سبعون": 70.0,
    "سبعين": 70.0,
    "ثمانون": 80.0,
    "ثمانين": 80.0,
    "تسعون": 90.0,
    "تسعين": 90.0,
    "مائة": 100.0,
    "مئة": 100.0,
    "مائتان": 200.0,
    "مئتان": 200.0,
    "مائتين": 200.0,
    "مئتين": 200.0,
}


def parse_arabic_number(s: str) -> float | None:
    """Parses numeric value from Arabic/English text cell, stripping citations and notes.

    Handles:
    - '100 دينار أردني [2]' -> 100.0
    - 'عشرة أيام عمل من تاريخ اكتمال المستندات [3]' -> 10.0
    - 'يومي عمل من اكتمال المستندات [1]' -> 2.0
    - 'خلال ساعة واحدة' -> 1.0
    - '25 JOD' -> 25.0
    """
    if not s:
        return None

    # 1. Strip citations like [1], [2], [1][2]
    s_clean = re.sub(r"\[\d+\]", "", s).strip()
    # Also strip markdown formatting
    s_clean = re.sub(r"[*_`]", "", s_clean).strip()

    # 2. Look for explicit digits (handles integers and decimals)
    digits = re.findall(r"\b\d+(?:[.,]\d+)?\b", s_clean.replace("،", "."))
    if digits:
        try:
            return float(digits[0].replace(",", "."))
        except ValueError:
            pass

    # 3. Match whole-word Arabic numerals
    tokens = set(re.findall(r"[\w]+", s_clean))
    for word, val in ARABIC_WORD_NUMBERS.items():
        if word in tokens:
            return val

    return None


def extract_explicit_charts(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Extracts explicit ```chart ... ``` or ```json:chart ... ``` blocks from text.

    Returns (cleaned_text_without_chart_blocks, list_of_chart_specs).
    """
    if not text:
        return text, []

    pattern = r"```(?:chart|json:chart|json)?\s*(\{.*?\})\s*```"
    charts: list[dict[str, Any]] = []

    def _replace(match: re.Match) -> str:
        chart_raw = match.group(1).strip()
        try:
            parsed = json.loads(chart_raw)
            if isinstance(parsed, dict) and "data" in parsed and isinstance(parsed["data"], list):
                # Verify that elements in data have label and value
                valid_data = [
                    d for d in parsed["data"]
                    if isinstance(d, dict) and "label" in d and "value" in d
                ]
                if len(valid_data) >= 1:
                    parsed["data"] = valid_data
                    charts.append(parsed)
                    return ""
        except Exception:
            pass
        return match.group(0)

    clean_text = re.sub(pattern, _replace, text, flags=re.DOTALL | re.IGNORECASE).strip()
    return clean_text, charts


def extract_charts_from_markdown_table(
    md_text: str, is_ar: bool = True
) -> list[dict[str, Any]]:
    """Synthesizes structured chart specs from Markdown tables containing numeric comparisons.

    Automatically identifies:
    - Fees / costs columns (دينار / JOD / رسوم)
    - SLA / Durations columns (أيام / ساعات / مدة / duration / SLA)
    - General quantitative metrics
    """
    if not md_text:
        return []

    charts: list[dict[str, Any]] = []
    lines = [
        l.strip()
        for l in md_text.splitlines()
        if l.strip().startswith("|") and l.strip().endswith("|")
    ]
    if len(lines) < 3:
        return []

    headers = [re.sub(r"[*_`]", "", c).strip() for c in lines[0].split("|")[1:-1]]
    rows: list[list[str]] = []
    for line in lines[2:]:
        # Skip markdown separator line
        if re.match(r"^[|\s:-]+$", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= len(headers):
            rows.append(cells[: len(headers)])

    if not rows or len(headers) < 2:
        return []

    NON_METRIC_KEYWORDS = [
        "مراجع", "مرجع", "reference", "citation",
        "فئة", "فئات", "حالة", "شروط", "شرط", "متطلب", "ملاحظ",
        "شكل مخرج", "مخرج", "category", "condition", "status", "notes"
    ]

    # Check if primary label column (col 0) has duplicate labels that need qualification from col 1
    col0_vals = [r[0].strip() for r in rows]
    has_col0_dups = len(col0_vals) != len(set(col0_vals))

    # Evaluate each candidate numeric column
    for col_idx in range(1, len(headers)):
        col_header = headers[col_idx]
        header_lower = col_header.lower()
        # Skip citations and qualifying non-metric metadata columns
        if any(k in header_lower or k in col_header for k in NON_METRIC_KEYWORDS):
            continue

        data: list[dict[str, Any]] = []
        for r in rows:
            lbl = r[0].strip()
            # If col 0 is identical across rows (e.g. 'إصدار وتجديد عادي'), qualify with col 1
            if has_col0_dups and len(r) > 1 and r[1] and r[1] not in ("ال يوجد", "لا يوجد", "-"):
                lbl = f"{r[0].strip()} ({r[1].strip()})"
            lbl = re.sub(r"\[\d+\]", "", lbl).strip()
            lbl = re.sub(r"[*_`]", "", lbl).strip()
            val = parse_arabic_number(r[col_idx])
            if val is not None and lbl:
                data.append({"label": lbl, "value": val})

        # At least 2 points to make a meaningful comparison chart
        if len(data) >= 2:
            # Determine metric label / units
            unit = ""
            if any(k in col_header for k in ["رسم", "رسوم", "دينار", "fee", "cost", "jod"]):
                unit = "دينار أردني" if is_ar else "JOD"
                title = f"مقارنة الرسوم ({col_header})" if is_ar else f"Fee Comparison ({col_header})"
            elif any(
                k in col_header
                for k in ["مدة", "إنجاز", "أيام", "ساعة", "زمن", "duration", "sla", "days", "hours"]
            ):
                unit = "أيام عمل / ساعات" if is_ar else "Business Days / Hours"
                title = f"مقارنة مدة الإنجاز ({col_header})" if is_ar else f"SLA / Duration Comparison ({col_header})"
            else:
                unit = col_header
                title = f"مقارنة {col_header}" if is_ar else f"Comparison: {col_header}"

            charts.append(
                {
                    "title": title,
                    "metric_label": unit,
                    "data": data,
                }
            )

    return charts


def extract_all_charts(text: str, is_ar: bool = True) -> tuple[str, list[dict[str, Any]]]:
    """Unified chart extractor.

    1. Extracts explicit ```chart ... ``` blocks.
    2. If no explicit charts found, inspects Markdown tables for numeric comparison columns.
    Returns (clean_text, list_of_chart_specs).
    """
    clean_text, explicit_charts = extract_explicit_charts(text)
    if explicit_charts:
        return clean_text, explicit_charts

    # Heuristic fallback: check markdown tables
    table_charts = extract_charts_from_markdown_table(clean_text, is_ar=is_ar)
    return clean_text, table_charts
