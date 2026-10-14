import pytest
from rag.ui.chart_extractor import (
    parse_arabic_number,
    extract_explicit_charts,
    extract_charts_from_markdown_table,
    extract_all_charts,
)


def test_parse_arabic_number():
    assert parse_arabic_number("100 دينار أردني [2]") == 100.0
    assert parse_arabic_number("50 دينار") == 50.0
    assert parse_arabic_number("25.5 JOD") == 25.5
    assert parse_arabic_number("عشرة أيام عمل من تاريخ اكتمال المستندات [3]") == 10.0
    assert parse_arabic_number("يومي عمل من اكتمال المستندات [1]") == 2.0
    assert parse_arabic_number("خلال ساعة واحدة") == 1.0
    assert parse_arabic_number("ساعتان [1]") == 2.0
    assert parse_arabic_number("خمسون دينار") == 50.0
    assert parse_arabic_number("نص غير رقمي بالكامل") is None


def test_extract_explicit_charts():
    text = (
        "هذه إجابة تجريبية.\n\n"
        "```chart\n"
        '{\n  "title": "مقارنة الرسوم",\n  "metric_label": "دينار",\n'
        '  "data": [\n    {"label": "مسار عادي", "value": 50},\n    {"label": "مسار مستعجل", "value": 100}\n  ]\n}\n'
        "```\n\n"
        "انتهت الإجابة."
    )
    clean_text, charts = extract_explicit_charts(text)
    assert len(charts) == 1
    assert charts[0]["title"] == "مقارنة الرسوم"
    assert charts[0]["data"][0]["value"] == 50
    assert charts[0]["data"][1]["value"] == 100
    assert "```chart" not in clean_text
    assert "هذه إجابة تجريبية." in clean_text
    assert "انتهت الإجابة." in clean_text


def test_extract_charts_from_markdown_table():
    md = (
        "| نوع المسار | الرسوم (الدينار الأردني) | مدة إنجاز الطلب | المراجع |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "| **المسار العادي** | 100 دينار أردني [2] | عشرة أيام عمل من تاريخ اكتمال المستندات [3] | [2][3] |\n"
        "| **المسار المستعجل** | 50 دينار أردني [2] | يومي عمل من اكتمال المستندات [1] | [1][2] |\n"
    )
    charts = extract_charts_from_markdown_table(md, is_ar=True)
    assert len(charts) == 2

    fees_chart = charts[0]
    assert "الرسوم" in fees_chart["title"]
    assert fees_chart["data"][0]["label"] == "المسار العادي"
    assert fees_chart["data"][0]["value"] == 100.0
    assert fees_chart["data"][1]["label"] == "المسار المستعجل"
    assert fees_chart["data"][1]["value"] == 50.0

    sla_chart = charts[1]
    assert "مدة الإنجاز" in sla_chart["title"]
    assert sla_chart["data"][0]["label"] == "المسار العادي"
    assert sla_chart["data"][0]["value"] == 10.0
    assert sla_chart["data"][1]["label"] == "المسار المستعجل"
    assert sla_chart["data"][1]["value"] == 2.0


def test_extract_all_charts_fallback():
    md = (
        "إليك جدول المقارنة:\n\n"
        "| Track | Fee | SLA |\n"
        "| --- | --- | --- |\n"
        "| Normal | 20 | 5 |\n"
        "| Express | 60 | 1 |\n"
    )
    clean_text, charts = extract_all_charts(md, is_ar=False)
    assert len(charts) == 2
    assert clean_text == md.strip()
    assert charts[0]["data"][0]["value"] == 20.0
    assert charts[1]["data"][1]["value"] == 1.0
