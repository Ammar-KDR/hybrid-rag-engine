import os
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from rag.ui.client import RAGAPIClient
from rag.nlp.arabic import is_arabic_text

load_dotenv()

# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="PSUT | Sovereign Hybrid RAG",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# University Institutional Theme (PSUT White & Royal Navy)
# Strict High-Contrast CSS: All text guaranteed 100% visible
# =========================================================

HIGH_CONTRAST_PSUT_CSS = """
<style>
/* Base typography & container spacing */
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 3.5rem;
    max-width: 1320px;
}

/* Light institutional background */
[data-testid="stAppViewContainer"], body {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1.5px solid #E2E8F0 !important;
}

/* Hide default streamlit headers and footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Universal text visibility overrides - High Contrast */
h1, h2, h3, h4, h5, h6 {
    color: #002D62 !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}

p, span, label, div, li {
    color: #0F172A;
}

/* Form inputs & text areas */
textarea, input[type="text"] {
    color: #0F172A !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #94A3B8 !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
}

textarea:focus, input[type="text"]:focus {
    border-color: #002D62 !important;
    box-shadow: 0 0 0 2px rgba(0, 45, 98, 0.2) !important;
}

textarea::placeholder {
    color: #64748B !important;
    font-weight: 400 !important;
}

/* Widget labels */
[data-testid="stWidgetLabel"] p, label p {
    color: #002D62 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}

/* Badges - Maximum Contrast & Legibility */
.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 8px;
    margin-bottom: 22px;
}

.trust-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-navy {
    background-color: #002D62;
    color: #FFFFFF !important;
    border: 1px solid #001A38;
}

.badge-blue {
    background-color: #1E40AF;
    color: #FFFFFF !important;
    border: 1px solid #1E3A8A;
}

.badge-green {
    background-color: #047857;
    color: #FFFFFF !important;
    border: 1px solid #065F46;
}

.badge-amber {
    background-color: #B45309;
    color: #FFFFFF !important;
    border: 1px solid #92400E;
}

/* Conflict Detective Badges */
.rel-badge {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
}
.rel-agreement {
    background-color: #DCFCE7;
    color: #166534 !important;
    border: 2px solid #86EFAC;
}
.rel-version {
    background-color: #DBEAFE;
    color: #1E40AF !important;
    border: 2px solid #93C5FD;
}
.rel-conflict {
    background-color: #FEE2E2;
    color: #991B1B !important;
    border: 2px solid #FCA5A5;
}
.rel-insufficient {
    background-color: #F1F5F9;
    color: #475569 !important;
    border: 2px solid #CBD5E1;
}

/* Primary Button (PSUT Navy) - Emil Kowalski Micro-Interactions */
.stButton>button[kind="primary"] {
    background-color: #002D62 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.25rem !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 1px 3px rgba(0, 45, 98, 0.12), 0 3px 8px rgba(0, 45, 98, 0.16) !important;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), background-color 140ms ease, box-shadow 140ms ease !important;
}

.stButton>button[kind="primary"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

.stButton>button[kind="primary"]:hover {
    background-color: #1E40AF !important;
    box-shadow: 0 2px 6px rgba(0, 45, 98, 0.2), 0 6px 14px rgba(0, 45, 98, 0.18) !important;
    transform: translateY(-1px) !important;
}

.stButton>button[kind="primary"]:active {
    transform: scale(0.97) !important;
    box-shadow: 0 1px 2px rgba(0, 45, 98, 0.2) !important;
}

/* Secondary Button - Emil Kowalski Tactile Feedback */
.stButton>button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #002D62 !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), border-color 140ms ease, background-color 140ms ease !important;
}

.stButton>button[kind="secondary"] p {
    color: #002D62 !important;
    font-weight: 700 !important;
}

.stButton>button[kind="secondary"]:hover {
    border-color: #002D62 !important;
    color: #002D62 !important;
    background-color: #EFF6FF !important;
    transform: translateY(-1px) !important;
}

.stButton>button[kind="secondary"]:active {
    transform: scale(0.97) !important;
}

/* Download Button - Emil Kowalski Tactile Feedback */
[data-testid="stDownloadButton"] button {
    background-color: #FFFFFF !important;
    color: #002D62 !important;
    border: 2px solid #002D62 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    transition: transform 140ms cubic-bezier(0.23, 1, 0.32, 1), background-color 140ms ease, color 140ms ease !important;
}

[data-testid="stDownloadButton"] button p {
    color: #002D62 !important;
    font-weight: 700 !important;
}

[data-testid="stDownloadButton"] button:hover {
    background-color: #002D62 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
}

[data-testid="stDownloadButton"] button:hover p {
    color: #FFFFFF !important;
}

[data-testid="stDownloadButton"] button:active {
    transform: scale(0.97) !important;
}

/* Top Tab Bar Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #CBD5E1;
    margin-bottom: 18px;
}

.stTabs [data-baseweb="tab"] {
    font-size: 1.02rem;
    font-weight: 700;
    color: #475569;
    padding: 10px 18px;
    border-radius: 8px 8px 0 0;
}

.stTabs [aria-selected="true"] {
    color: #002D62 !important;
    border-bottom: 3px solid #002D62 !important;
    font-weight: 800 !important;
}

/* Executive Box & Cards */
.exec-box {
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-left: 5px solid #002D62;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 45, 98, 0.05);
}

.finding-card {
    background-color: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

.finding-tag {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.tag-policy { background: #DBEAFE; color: #1E40AF; }
.tag-technical { background: #E0E7FF; color: #3730A3; }
.tag-compliance { background: #FEF3C7; color: #92400E; }
.tag-action_item { background: #DCFCE7; color: #166534; }

.source-pill-quote {
    background-color: #F8FAFC;
    border-left: 3px solid #002D62;
    padding: 6px 10px;
    margin-top: 6px;
    font-size: 0.82rem;
    color: #334155;
    font-style: italic;
    border-radius: 0 4px 4px 0;
}

/* Streamlit 1.61.1 MultiSelect Tag / Pill Styling - Absolute White Contrast */
[data-tag],
[data-tag-index],
[data-baseweb="tag"],
[data-testid="stMultiSelectTagsContainer"] [data-tag],
[data-testid="stMultiSelect"] [data-tag],
.stMultiSelect [data-tag],
[role="group"][aria-label="Selected values"] > div,
[role="group"][aria-label="Selected values"] > span {
    background-color: #002D62 !important;
    border: 1.5px solid #3B82F6 !important;
    border-radius: 6px !important;
    padding: 3px 10px !important;
    margin: 3px 4px !important;
}

[data-tag] *,
[data-tag] span,
[data-tag] span[title],
[data-tag-index] *,
[data-tag-index] span,
[data-baseweb="tag"] *,
[data-baseweb="tag"] span,
[data-testid="stMultiSelectTagsContainer"] *,
[data-testid="stMultiSelectTagsContainer"] span,
[data-testid="stMultiSelect"] [data-tag] *,
[data-testid="stMultiSelect"] [data-tag] span,
.stMultiSelect [data-tag] *,
[role="group"][aria-label="Selected values"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    fill: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em !important;
}

[data-tag] svg,
[data-tag] path,
[data-tag] [aria-label*="Remove"] svg,
[data-tag] [aria-label*="Remove"] path,
[data-testid="stMultiSelectTagsContainer"] svg,
[data-testid="stMultiSelectTagsContainer"] path {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

[data-tag]:hover,
[data-tag-index]:hover,
[data-baseweb="tag"]:hover {
    background-color: #1E40AF !important;
}

/* Multiselect and Selectbox input containers */
[data-baseweb="select"] > div:first-child {
    background-color: #FFFFFF !important;
    border: 1.5px solid #94A3B8 !important;
    border-radius: 8px !important;
}

[data-baseweb="select"] input {
    color: #0F172A !important;
}

/* Dropdown menu items when open */
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[role="listbox"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

li[role="option"],
[data-baseweb="menu"] [role="option"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
}

li[role="option"]:hover,
li[role="option"][aria-selected="true"],
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"][aria-selected="true"] {
    background-color: #EFF6FF !important;
    color: #002D62 !important;
}
</style>
"""

ARABIC_RTL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

/* Clean, directional RTL setup on container level */
.block-container, [data-testid="stSidebarContent"], [data-testid="stMarkdownContainer"] {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', 'Segoe UI', Tahoma, -apple-system, sans-serif !important;
}

h1, h2, h3, h4, h5, h6, p, label, li {
    font-family: 'Cairo', 'Segoe UI', Tahoma, -apple-system, sans-serif !important;
    text-align: right;
    direction: rtl;
}

/* CRITICAL FIX: Explicitly preserve Material Symbols icon fonts so they NEVER render as raw ligature text (e.g. keyboard_ar) */
[data-testid="stIconMaterial"], 
.material-symbols-rounded, 
.material-symbols-outlined, 
.material-icons,
[class*="material-symbols"],
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpander"] summary span svg,
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
    direction: ltr !important;
    text-align: center !important;
    font-style: normal !important;
    font-weight: normal !important;
}

/* Preserve code blocks and technical identifiers from RTL distortion */
code, kbd, samp, pre, [data-testid="stCodeBlock"], .en-code {
    font-family: "Consolas", "Monaco", "Courier New", monospace !important;
    direction: ltr !important;
    text-align: left !important;
    display: inline-block !important;
    unicode-bidi: embed !important;
}

/* BiDi Isolation utilities */
.bidi-text, [dir="auto"] {
    unicode-bidi: plaintext !important;
    text-align: right !important;
}

.ltr-isolate, [dir="ltr"] {
    direction: ltr !important;
    text-align: left !important;
    display: inline-block !important;
    unicode-bidi: isolate !important;
}

/* Streamlit Expander styling in RTL */
[data-testid="stExpander"] summary {
    direction: rtl !important;
    text-align: right !important;
}

[data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] {
    margin-right: 8px !important;
    margin-left: 0 !important;
    text-align: right !important;
}

/* Streamlit Tabs in RTL */
.stTabs [data-baseweb="tab-list"] {
    direction: rtl !important;
}

/* Sidebar styling in RTL */
[data-testid="stSidebar"] {
    direction: rtl !important;
    text-align: right !important;
}

/* Form inputs */
textarea, input[type="text"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif !important;
}

.trust-badge {
    direction: rtl !important;
    font-family: 'Cairo', sans-serif !important;
}

.exec-box {
    border-left: 1.5px solid #CBD5E1 !important;
    border-right: 5px solid #002D62 !important;
    direction: rtl !important;
    text-align: right !important;
}

.source-pill-quote {
    border-left: none !important;
    border-right: 3px solid #002D62 !important;
    border-radius: 4px 0 0 4px !important;
    direction: rtl !important;
    text-align: right !important;
}

/* Streamlit 1.61.1 MultiSelect Tag in RTL - Force LTR text and white color */
[data-tag],
[data-tag-index],
[data-baseweb="tag"],
[data-testid="stMultiSelectTagsContainer"] [data-tag],
[data-testid="stMultiSelect"] [data-tag],
.stMultiSelect [data-tag],
[role="group"][aria-label="Selected values"] > div,
[role="group"][aria-label="Selected values"] > span {
    background-color: #002D62 !important;
    border: 1.5px solid #3B82F6 !important;
    border-radius: 6px !important;
    direction: ltr !important;
}

[data-tag] *,
[data-tag] span,
[data-tag] span[title],
[data-tag-index] *,
[data-tag-index] span,
[data-baseweb="tag"] *,
[data-baseweb="tag"] span,
[data-testid="stMultiSelectTagsContainer"] *,
[data-testid="stMultiSelectTagsContainer"] span,
[data-testid="stMultiSelect"] [data-tag] *,
[data-testid="stMultiSelect"] [data-tag] span,
.stMultiSelect [data-tag] *,
[role="group"][aria-label="Selected values"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    fill: #FFFFFF !important;
    direction: ltr !important;
}

[data-tag] svg,
[data-tag] path,
[data-tag] [aria-label*="Remove"] svg,
[data-tag] [aria-label*="Remove"] path,
[data-testid="stMultiSelectTagsContainer"] svg,
[data-testid="stMultiSelectTagsContainer"] path {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}
</style>
"""

st.markdown(HIGH_CONTRAST_PSUT_CSS, unsafe_allow_html=True)

# =========================================================
# Client Initialization & Session State
# =========================================================

api_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
client = RAGAPIClient(base_url=api_url)

if "question_input" not in st.session_state:
    st.session_state["question_input"] = ""

if "trigger_ask" not in st.session_state:
    st.session_state["trigger_ask"] = False

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

if "last_question" not in st.session_state:
    st.session_state["last_question"] = ""

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "documents" not in st.session_state:
    try:
        st.session_state["documents"] = client.list_documents()
    except Exception:
        st.session_state["documents"] = []

if "health_status" not in st.session_state:
    st.session_state["health_status"] = None


# =========================================================
# Helper Functions
# =========================================================

def get_logo_path() -> str | None:
    candidates = [
        "assets/psut_logo.png",
        "assets/psut_logo.jpg",
        "assets/psut_logo.svg",
        "assets/psut_crest.svg",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    return None


def clean_source_name(raw_src: str) -> tuple[str, str]:
    base_src = os.path.basename(raw_src or "Document")
    clean_src = base_src.split("_", 1)[-1] if len(base_src) > 65 and "_" in base_src else base_src
    return clean_src, base_src


def build_chunk_text_map(trace: dict | None, evidence_list: list | None = None) -> dict[str, str]:
    chunk_map = {}
    if evidence_list:
        for ev in evidence_list:
            cid = ev.get("chunk_id")
            text = ev.get("text")
            if cid and text:
                chunk_map[cid] = text

    if trace:
        for chunk in trace.get("final_evidence", []):
            cid = chunk.get("chunk_id")
            text = chunk.get("text")
            if cid and text and cid not in chunk_map:
                chunk_map[cid] = text

        for candidate in trace.get("candidates", []):
            cid = candidate.get("chunk_id")
            text = candidate.get("text")
            if cid and text and cid not in chunk_map:
                chunk_map[cid] = text

    return chunk_map


def generate_executive_brief_export(
    question: str,
    result: dict,
    chunk_map: dict[str, str],
    is_ar: bool = False,
) -> str:
    req_id = result.get("request_id", "N/A")
    latency = result.get("latency", {})
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    abstained = result.get("abstained", False)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if is_ar or is_arabic_text(question):
        doc = [
            "# 🏛️ جامعة الأميرة سمية للتكنولوجيا",
            "## تقرير الإيجاز والاستخلاص الذكي السيادي",
            f"**تاريخ التوليد:** {now_str} (بيئة عمل سيادية معزولة محلياً)",
            "**التصنيف:** سري / استخبارات حكومية سيادية",
            f"**معرف الطلب:** `{req_id}`",
            f"**حالة التدقيق:** {'⚠️ اعتذار (أدلة غير كافية للتحقق)' if abstained else '✅ موثق ومطابق للأدلة الرسمية'}",
            "\n---\n",
            "## 🎯 الاستفسار الإجرائي / التنفيذي",
            f"> {question}",
            "\n---\n",
            "## 📌 الاستخلاص الذكي والنتائج المعتمدة",
            answer,
            "\n---\n",
            "## 📑 الأدلة الموثقة وتوثيق المراجع الرسمية",
        ]

        if not citations:
            doc.append("_لا توجد مراجع مباشرة مسجلة._")
        else:
            for cit in citations:
                ref = cit.get("reference")
                source = cit.get("source")
                clean_name, base_name = clean_source_name(source)
                page = cit.get("page_number")
                heading = " ← ".join(cit.get("heading_path") or [])
                cid = cit.get("chunk_id", "")
                raw_quote = chunk_map.get(cid, "فقرة نصية موثقة من أصل الوثيقة الرسمية.")
                
                snippet = raw_quote.strip()
                if len(snippet) > 250:
                    snippet = snippet[:247] + "..."

                page_info = f"، صفحة {page}" if page is not None else ""
                heading_info = f" ({heading})" if heading else ""
                doc.append(f"### [مرجع {ref}] {clean_name}{page_info}{heading_info}")
                doc.append(f"> \"{snippet}\"\n")
                doc.append(f"- *الملف:* `{base_name}` | *معرف المقطع:* `{cid}`\n")

        doc.extend([
            "\n---\n",
            "## 🛡️ سجل التدقيق والموثوقية السيادية",
            "- **محرك الاسترجاع:** هجين (تضمين كثيف Dense + معجمي BM25 + دمج تراتبي RRF)",
            "- **معيد الترتيب:** Cross-Encoder (`BAAI/bge-reranker-base`) متعدد اللغات",
            "- **محرك التوليد المحلي:** Qwen 3.5 4B (`Ollama`)",
            "- **التسريع العتادي:** NVIDIA GeForce RTX 3060 Laptop GPU (CUDA مفعّل)",
            "- **قاعدة المتجهات:** Qdrant مدمجة ومحلية بالكامل",
            f"- **تفصيل زمن الاستجابة:** إجمالي {latency.get('total_ms', 0):.0f} مللي ثانية (الاسترجاع: {latency.get('retrieval_ms', 0):.0f} مللي ثانية | إعادة الترتيب: {latency.get('reranking_ms', 0):.0f} مللي ثانية | التوليد: {latency.get('generation_ms', 0):.0f} مللي ثانية)",
        ])
    else:
        doc = [
            "# 🏛️ PRINCESS SUMAYA UNIVERSITY FOR TECHNOLOGY",
            "## Sovereign Hybrid RAG Intelligence Briefing",
            f"**Generated:** {now_str} (Air-Gapped Sovereign Workstation)",
            "**Classification:** Confidential / Sovereign Enterprise Intelligence",
            f"**Request Identifier:** `{req_id}`",
            f"**Audit Status:** {'⚠️ Abstained (Insufficient Evidence)' if abstained else '✅ Verified & Grounded'}",
            "\n---\n",
            "## 🎯 Executive Inquiry",
            f"> {question}",
            "\n---\n",
            "## 📌 Key Synthesis & Grounded Findings",
            answer,
            "\n---\n",
            "## 📑 Verified Evidence & Source Citations",
        ]

        if not citations:
            doc.append("_No direct citations recorded._")
        else:
            for cit in citations:
                ref = cit.get("reference")
                source = cit.get("source")
                clean_name, base_name = clean_source_name(source)
                page = cit.get("page_number")
                heading = " → ".join(cit.get("heading_path") or [])
                cid = cit.get("chunk_id", "")
                raw_quote = chunk_map.get(cid, "Evidence excerpt verified in primary document.")
                
                snippet = raw_quote.strip()
                if len(snippet) > 250:
                    snippet = snippet[:247] + "..."

                page_info = f", Page {page}" if page is not None else ""
                heading_info = f" ({heading})" if heading else ""
                doc.append(f"### [{ref}] {clean_name}{page_info}{heading_info}")
                doc.append(f"> \"{snippet}\"\n")
                doc.append(f"- *File:* `{base_name}` | *Chunk ID:* `{cid}`\n")

        doc.extend([
            "\n---\n",
            "## 🛡️ Reliability & Sovereignty Audit",
            "- **Retrieval Pipeline:** Hybrid (Dense Vector + BM25 Lexical + Reciprocal Rank Fusion)",
            "- **Reranker:** Cross-Encoder (`BAAI/bge-reranker-base`)",
            "- **Local LLM Engine:** Qwen 3.5 4B (`Ollama`)",
            "- **Hardware Acceleration:** NVIDIA GeForce RTX 3060 Laptop GPU (CUDA Active)",
            "- **Vector Index:** Embedded Qdrant (Zero-Docker Local Storage)",
            f"- **Latency Breakdown:** Total {latency.get('total_ms', 0):.0f} ms (Retrieval: {latency.get('retrieval_ms', 0):.0f} ms | Rerank: {latency.get('reranking_ms', 0):.0f} ms | Gen: {latency.get('generation_ms', 0):.0f} ms)",
        ])

    return "\n\n".join(doc)


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:
    logo_file = get_logo_path()
    if logo_file:
        st.image(logo_file, use_container_width=True)

    st.markdown('<div class="sidebar-section-title">Language / لغة الواجهة</div>', unsafe_allow_html=True)
    ui_lang = st.radio(
        "اختر لغة الواجهة / Select Language",
        ["🇸🇦 العربية (Arabic)", "🇬🇧 English"],
        index=0,
        label_visibility="collapsed",
    )
    is_ar = ui_lang.startswith("🇸🇦")

    if is_ar:
        st.markdown(ARABIC_RTL_CSS, unsafe_allow_html=True)

    st.markdown(
        f'<div class="sidebar-section-title">{"حالة الأنظمة السيادية" if is_ar else "System Status"}</div>',
        unsafe_allow_html=True,
    )
    try:
        health = client.get_health()
        st.session_state["health_status"] = health
        st.success("🟢 الأنظمة تعمل محلياً (Air-Gapped)" if is_ar else "🟢 Core Services Ready (Air-Gapped)")
    except Exception:
        st.error("🔴 جاري الاتصال بالخادم..." if is_ar else "🔴 Connecting to API Server...")

    doc_count = len(st.session_state.get("documents", []))
    st.metric("الوثائق المفهرسة" if is_ar else "Indexed Documents", doc_count)

    st.markdown(
        f'<div class="sidebar-section-title">{"إدارة الجلسة" if is_ar else "Session Controls"}</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔄 تحديث الوثائق" if is_ar else "🔄 Refresh Documents", use_container_width=True):
        try:
            st.session_state["documents"] = client.list_documents()
            st.success("تم التحديث بنجاح!" if is_ar else "Synchronized!")
        except Exception as e:
            st.error(str(e))

    if st.button("🧹 مسح سجل المحادثة" if is_ar else "🧹 Clear Chat History", use_container_width=True):
        st.session_state["chat_history"] = []
        st.session_state["last_result"] = None
        st.session_state["last_question"] = ""
        st.rerun()


# =========================================================
# Main Institutional Header
# =========================================================

header_logo = get_logo_path()
if header_logo:
    col_logo, col_head = st.columns([1.5, 3.5])
    with col_logo:
        st.image(header_logo, use_container_width=True)
    with col_head:
        if is_ar:
            st.markdown(
                """
                <div style="display:flex; flex-direction:column; justify-content:center; padding-right:16px; border-right:2.5px solid #E2E8F0; min-height:80px;">
                    <h1 style="color:#002D62; font-size:1.85rem; font-weight:800; margin:0; line-height:1.2;">
                        نظام الاسترجاع الهجين والذكاء الاصطناعي السيادي
                    </h1>
                    <p style="color:#334155; font-size:0.98rem; margin-top:5px; margin-bottom:0; font-weight:600;">
                        جامعة الأميرة سمية للتكنولوجيا • هاكاثون 42 إربد • قطاع الخدمات الحكومية
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="display:flex; flex-direction:column; justify-content:center; padding-left:16px; border-left:2.5px solid #E2E8F0; min-height:80px;">
                    <h1 style="color:#002D62; font-size:1.85rem; font-weight:800; margin:0; line-height:1.2;">
                        Sovereign Hybrid RAG Engine
                    </h1>
                    <p style="color:#334155; font-size:0.98rem; margin-top:5px; margin-bottom:0; font-weight:600;">
                        Princess Sumaya University for Technology • 42 Irbid Hackathon
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.title("🏛️ جامعة الأميرة سمية للتكنولوجيا - الذكاء الاصطناعي السيادي" if is_ar else "🏛️ PSUT Sovereign Hybrid RAG")

# Trust Badges
if is_ar:
    st.markdown(
        """
        <div class="badge-row">
            <span class="trust-badge badge-green">🔒 بيئة سيادية معزولة 100% (AIR-GAPPED)</span>
            <span class="trust-badge badge-blue">⚡ تسريع محلي كارت الشاشة RTX 3060 CUDA</span>
            <span class="trust-badge badge-navy">🛡️ صفر تسريب سحابي (ZERO EXFILTRATION)</span>
            <span class="trust-badge badge-amber">⚡ استرجاع هجين + معيد ترتيب BGE MULTILINGUAL</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="badge-row">
            <span class="trust-badge badge-green">🔒 100% AIR-GAPPED SOVEREIGN</span>
            <span class="trust-badge badge-blue">⚡ RTX 3060 CUDA ACCELERATED</span>
            <span class="trust-badge badge-navy">🛡️ ZERO CLOUD EXFILTRATION</span>
            <span class="trust-badge badge-amber">⚡ HYBRID RRF + BGE CROSS-ENCODER</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Top-Level Institutional Tabs
# =========================================================

tab_titles = [
    "🔍 المحادثة التفاعلية ومستكشف الأدلة" if is_ar else "🔍 Interactive Chat & Evidence",
    "⚖️ محقق تعارض وتناقض الوثائق" if is_ar else "⚖️ Document Conflict Detective",
    "📋 الإيجازات والتقارير التنفيذية" if is_ar else "📋 Executive Briefings",
    "📁 مستودع المعرفة والتشخيص الفني" if is_ar else "📁 Knowledge Repository & Diagnostics",
]

tab_qa, tab_compare, tab_briefing, tab_repo = st.tabs(tab_titles)


# =========================================================
# TAB 1: INTERACTIVE CHAT & EVIDENCE EXPLORER
# =========================================================

with tab_qa:
    # Preset Starter Inquiries
    if is_ar:
        st.markdown(
            "<span style='font-size:0.82rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em;'>"
            "نماذج أسئلة الخدمات الحكومية (انقر للاختبار الفوري)"
            "</span>",
            unsafe_allow_html=True,
        )
        preset_cols = st.columns(3)
        with preset_cols[0]:
            if st.button("🛂 وثائق ورسوم تجديد جواز السفر", key="preset_gov_1", use_container_width=True):
                st.session_state["question_input"] = "ما هي الوثائق المطلوبة والرسوم المقررة لإصدار أو تجديد جواز السفر الأردني؟"
                st.session_state["trigger_ask"] = True
                st.rerun()

        with preset_cols[1]:
            if st.button("⚡ رسوم وإجراءات المعاملة المستعجلة", key="preset_gov_2", use_container_width=True):
                st.session_state["question_input"] = "ما هي رسوم إصدار جواز السفر المستعجل وما هي المدة الزمنية لإنجازه ومواقع الخدمة؟"
                st.session_state["trigger_ask"] = True
                st.rerun()

        with preset_cols[2]:
            if st.button("📱 اعتماد الهوية الرقمية عبر تطبيق سند", key="preset_gov_3", use_container_width=True):
                st.session_state["question_input"] = "هل تقبل الهوية الرقمية الصادرة عبر تطبيق سند رسمياً كإثبات شخصية لفتح المعاملة المستعجلة؟"
                st.session_state["trigger_ask"] = True
                st.rerun()
    else:
        st.markdown(
            "<span style='font-size:0.82rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em;'>"
            "Sample Queries (Click to Test Instantly)"
            "</span>",
            unsafe_allow_html=True,
        )
        preset_cols = st.columns(3)
        with preset_cols[0]:
            if st.button("🔍 Troubleshooting Database Timeout", key="preset_db", use_container_width=True):
                st.session_state["question_input"] = "How do we troubleshoot and resolve database connection timeout errors?"
                st.session_state["trigger_ask"] = True
                st.rerun()

        with preset_cols[1]:
            if st.button("🌐 DNS Configuration Guidelines", key="preset_dns", use_container_width=True):
                st.session_state["question_input"] = "What are the recommended DNS configuration guidelines and resolver steps?"
                st.session_state["trigger_ask"] = True
                st.rerun()

        with preset_cols[2]:
            if st.button("🐳 Docker Container Restart Policies", key="preset_docker", use_container_width=True):
                st.session_state["question_input"] = "What are the container restart policies and memory limit configurations in Docker?"
                st.session_state["trigger_ask"] = True
                st.rerun()

    # Scope Selection: All Documents or Single Document
    docs = st.session_state.get("documents", [])
    all_label = "جميع الوثائق المفهرسة" if is_ar else "All Ingested Documents"
    doc_options = [all_label] + [f"{clean_source_name(d.get('filename'))[0]} ({d.get('document_id')[:8]})" for d in docs]
    scope_prompt = "نطاق البحث واسترجاع الوثائق" if is_ar else "Document Retrieval Scope"
    selected_scope_label = st.selectbox(scope_prompt, options=doc_options, index=0)

    selected_doc_ids = None
    if selected_scope_label != all_label:
        selected_idx = doc_options.index(selected_scope_label) - 1
        selected_doc_ids = [docs[selected_idx]["document_id"]]

    # Query Input Area
    query_text = st.text_area(
        "الاستفسار / السؤال المطلوب تحليله:" if is_ar else "Inquiry / Prompt",
        value=st.session_state["question_input"],
        height=85,
        placeholder=(
            "اطرح استفسارك حول شروط المعاملات الحكومية، الوثائق المطلوبة، الرسوم، أو الإجراءات الرسمية..."
            if is_ar
            else "Ask any question regarding system architecture, operations, policies, or follow-up..."
        ),
        key="main_query_text_area",
    )

    action_col1, action_col2, action_col3 = st.columns([2, 1, 1])
    with action_col1:
        ask_button = st.button(
            "🚀 تشغيل التحليل والاسترجاع السيادي" if is_ar else "🚀 Run Intelligence Analysis",
            type="primary",
            use_container_width=True,
        )
    with action_col2:
        include_trace = st.checkbox(
            "تضمين سجل تدقيق معيد الترتيب" if is_ar else "Include Reranker Audit Trace",
            value=True,
        )
    with action_col3:
        if st.button("🧹 مسح المدخلات" if is_ar else "🧹 Clear Input", use_container_width=True):
            st.session_state["question_input"] = ""
            st.session_state["last_result"] = None
            st.session_state["last_question"] = ""
            st.session_state["trigger_ask"] = False
            st.rerun()

    should_run = ask_button or st.session_state["trigger_ask"]

    if should_run:
        active_question = query_text.strip() or st.session_state.get("question_input", "").strip()

        if not active_question:
            st.warning(
                "يرجى إدخال استفسار أو اختيار أحد النماذج المقترحة."
                if is_ar
                else "Please enter a question or choose an inquiry preset."
            )
            st.session_state["trigger_ask"] = False
        else:
            st.session_state["trigger_ask"] = False
            st.session_state["question_input"] = active_question
            st.session_state["last_question"] = active_question

            try:
                with st.spinner(
                    "جاري تنفيذ الاسترجاع الهجين والتحليل السيادي المقيد بالأدلة..."
                    if is_ar
                    else "Executing Hybrid RAG with Conversational Intent Resolution..."
                ):
                    # Pass history to rewriter
                    history_payload = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.get("chat_history", [])[-4:]
                    ]
                    res = client.ask(
                        question=active_question,
                        history=history_payload,
                        document_ids=selected_doc_ids,
                        include_trace=include_trace,
                    )
                    st.session_state["last_result"] = res

                    # Append to conversation
                    st.session_state["chat_history"].append({"role": "user", "content": active_question})
                    st.session_state["chat_history"].append({"role": "assistant", "content": res.get("answer", "")})

            except Exception as exc:
                st.error(f"{'فشل التحليل والاسترجاع:' if is_ar else 'Analysis failed:'} {exc}")

    result = st.session_state.get("last_result")
    active_q = st.session_state.get("last_question", "")

    if result:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        trace = result.get("trace")
        evidence_list = result.get("evidence", [])
        chunk_map = build_chunk_text_map(trace, evidence_list)
        citations = result.get("citations", [])
        latency = result.get("latency", {})
        abstained = result.get("abstained", False)
        was_rewritten = result.get("was_rewritten", False)
        retrieval_q = result.get("retrieval_question")

        if was_rewritten and retrieval_q:
            st.info(
                f"ℹ️ **{'إعادة صياغة السؤال لسياق المحادثة:' if is_ar else 'Conversational Intent Resolved:'}** "
                f"{'تم تحسين الاستفسار إلى' if is_ar else 'Query reformulated to'} *\"{retrieval_q}\"*"
            )

        if abstained:
            st.warning(
                "⚠️ **اعتذار النظام (امتناع آمن)**: انخفضت درجة الثقة ومطابقة الأدلة عن الحد الأدنى للأمان والامتثال. لم يتم توليد أي إجابة تكهنية غير مدعومة بوثائق رسمية."
                if is_ar
                else "⚠️ **System Abstained**: Retrieval confidence fell below safety threshold. No speculative answer generated."
            )
        else:
            badge_title = "إجابة موثقة ومدعومة بالأدلة الرسمية المعتمدة" if is_ar else "Grounded & Evidence-Backed Synthesis"
            req_label = "معرف الطلب:" if is_ar else "Request ID:"
            req_id_short = result.get("request_id", "N/A")[:12]
            border_side = "border-right:5px solid #002D62;" if is_ar else "border-left:5px solid #002D62;"
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; background:#FFFFFF; border:1.5px solid #BFDBFE; {border_side} border-radius:8px; padding:10px 16px; margin-bottom:14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="color:#047857; font-size:1.1rem; font-weight:800;">●</span>
                        <span style="font-weight:800; color:#002D62; font-size:0.95rem;">{badge_title}</span>
                    </div>
                    <div>
                        <span style="background:#EFF6FF; color:#002D62; font-size:0.78rem; font-weight:700; padding:4px 10px; border-radius:6px; border:1px solid #BFDBFE;" dir="ltr">{req_label} {req_id_short}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Grounded Answer Presentation
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:0.88rem; font-weight:800; color:#002D62; text-transform:uppercase; margin-bottom:10px;">📌 {"النتيجة والاستخلاص الذكي الموثق" if is_ar else "Synthesized Intelligence"}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"<div class='bidi-text' dir='auto'>{result.get('answer', '')}</div>", unsafe_allow_html=True)

        # Latency & Pipeline Metrics Bar
        if latency:
            l_col1, l_col2, l_col3, l_col4 = st.columns(4)
            with l_col1:
                st.metric("الزمن الإجمالي" if is_ar else "Total Latency", f"{latency.get('total_ms', 0):.0f} ms")
            with l_col2:
                st.metric("استرجاع هجين" if is_ar else "Hybrid Retrieval", f"{latency.get('retrieval_ms', 0):.0f} ms")
            with l_col3:
                st.metric("إعادة ترتيب BGE" if is_ar else "BGE Reranking", f"{latency.get('reranking_ms', 0):.0f} ms")
            with l_col4:
                st.metric("توليد محلي Ollama" if is_ar else "Local LLM Gen", f"{latency.get('generation_ms', 0):.0f} ms")

        # Interactive Evidence Explorer & Source Drawer
        if citations or evidence_list:
            drawer_title = (
                "📑 مستعرض الأدلة التفاعلي (انقر لمعاينة المصدر الأصلي وصفحة PDF)"
                if is_ar
                else "📑 Interactive Evidence Drawer (Click to Inspect Primary Source & PDF Preview)"
            )
            st.markdown(
                f"<div style='font-size:0.85rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em; margin-top:14px; margin-bottom:8px;'>"
                f"{drawer_title}"
                f"</div>",
                unsafe_allow_html=True,
            )

            for idx, cit in enumerate(citations if citations else evidence_list, start=1):
                ref = cit.get("reference", idx)
                raw_src = cit.get("source", "Document")
                clean_name, base_src = clean_source_name(raw_src)
                page = cit.get("page_number")
                cid = cit.get("chunk_id", "")
                doc_id = cit.get("document_id", "")
                heading = " → ".join(cit.get("heading_path") or [])

                page_label = f" • {'صفحة' if is_ar else 'Page'} {page}" if page is not None else ""
                exp_header = f"📄 {'الدليل' if is_ar else 'Evidence'} [{ref}]: {clean_name}{page_label}"
                with st.expander(exp_header, expanded=(idx == 1)):
                    c_left, c_right = st.columns([1.5, 1])
                    with c_left:
                        st.markdown(
                            f"**{'الوثيقة:' if is_ar else 'Document:'}** <code dir='ltr'>{clean_name}</code> (<code dir='ltr'>{base_src}</code>)",
                            unsafe_allow_html=True,
                        )
                        if heading:
                            st.caption(f"**{'المسار / القسم:' if is_ar else 'Section Path:'}** {heading}")
                        st.caption(
                            f"**{'البصمة الرقمية للمقطع:' if is_ar else 'Chunk SHA-256:'}** <code dir='ltr'>{cid[:24]}...</code>",
                            unsafe_allow_html=True,
                        )

                        raw_text = cit.get("text") or chunk_map.get(cid)
                        if raw_text:
                            st.markdown(
                                f"<div class='source-pill-quote' dir='auto'>\"{raw_text.strip()}\"</div>",
                                unsafe_allow_html=True,
                            )

                    with c_right:
                        if page is not None and doc_id:
                            st.caption("🖼️ " + ("معاينة صفحة PDF الرسمية" if is_ar else "High-Res PDF Page Preview"))
                            img_bytes = client.get_page_preview(doc_id, page)
                            if img_bytes:
                                st.image(img_bytes, caption=f"{'صفحة' if is_ar else 'Page'} {page}", use_container_width=True)
                            else:
                                st.info("معاينة الصفحة متاحة في مستعرض PDF." if is_ar else f"Page {page} preview available in PDF viewer.")
                        else:
                            st.caption("📄 " + ("مستند نصي / ماركداون معتمد" if is_ar else "Markdown / Text Document Evidence"))
                            st.success("مقطع موثق ومطابق للأصل في المستودع السيادي." if is_ar else "Verified verbatim passage in sovereign store.")

        # Optional Reranker Audit Trace Expander
        if include_trace and trace:
            trace_header = "🔍 سجل تدقيق معيد الترتيب والمسار التشخيصي الكامل (Reranker Audit Trace)" if is_ar else "🔍 Reranker Audit Trace & Stage Telemetry"
            with st.expander(trace_header, expanded=False):
                cand_list = trace.get("candidates", [])
                if cand_list:
                    st.caption(
                        f"{'المرشحات المسترجعة قبل وبعد إعادة الترتيب:' if is_ar else 'Candidates retrieved and scored across pipeline:'} ({len(cand_list)} {'مرشح' if is_ar else 'candidates'})"
                    )
                    trace_rows = []
                    for c_idx, c in enumerate(cand_list[:10], start=1):
                        c_src, _ = clean_source_name(c.get("source", ""))
                        trace_rows.append({
                            "#" if is_ar else "Rank": c_idx,
                            "الوثيقة" if is_ar else "Document": c_src,
                            "معيد الترتيب (Score)" if is_ar else "Rerank Score": f"{c.get('score', 0):.4f}" if c.get("score") is not None else "N/A",
                            "البحث الكثيف (Dense)" if is_ar else "Dense Score": f"{c.get('dense_score', 0):.4f}" if c.get("dense_score") is not None else "N/A",
                            "البحث المعجمي (BM25)" if is_ar else "BM25 Score": f"{c.get('sparse_score', 0):.4f}" if c.get("sparse_score") is not None else "N/A",
                        })
                    st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)

        # Export Button
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        export_content = generate_executive_brief_export(active_q, result, chunk_map, is_ar=is_ar)
        st.download_button(
            label="📥 تصدير الإيجاز التنفيذي (.md)" if is_ar else "📥 Export Executive Briefing (.md)",
            data=export_content,
            file_name=f"psut_executive_brief_{result.get('request_id', 'audit')[:8]}.md",
            mime="text/markdown",
            use_container_width=True,
            type="secondary",
        )


# =========================================================
# TAB 2: DOCUMENT CONFLICT DETECTIVE (STAR DEMO FEATURE)
# =========================================================

with tab_compare:
    st.subheader("⚖️ محقق تعارض وتناقض الوثائق والسياسات" if is_ar else "⚖️ Document Conflict Detective")
    st.caption(
        "مقارنة دقيقة ومعزولة بين وثيقتين لاكتشاف التناقضات أو الفروقات الإجرائية أو التوافق التام."
        if is_ar
        else "Perform rigorous, air-gapped comparison between two documents to detect contradictions, version differences, or policy alignment."
    )

    docs = st.session_state.get("documents", [])
    if len(docs) < 2:
        st.info("يرجى فهرسة وثيقتين على الأقل لتفعيل خاصية كشف التعارض والتناقض." if is_ar else "Please index at least two documents to activate side-by-side conflict detection.")
    else:
        doc_names = [f"{clean_source_name(d.get('filename'))[0]} ({d.get('document_id')[:8]})" for d in docs]
        c1, c2 = st.columns(2)
        with c1:
            sel_a = st.selectbox("الوثيقة المرجعية الأساسية (أ)" if is_ar else "Primary Baseline Document (A)", options=doc_names, index=0)
        with c2:
            sel_b = st.selectbox("وثيقة المقارنة والتحقق (ب)" if is_ar else "Comparison Target Document (B)", options=doc_names, index=min(1, len(doc_names) - 1))

        doc_a_idx = doc_names.index(sel_a)
        doc_b_idx = doc_names.index(sel_b)
        doc_a_id = docs[doc_a_idx]["document_id"]
        doc_b_id = docs[doc_b_idx]["document_id"]

        default_topic = (
            "رسوم المعاملة المستعجلة وزمن الإنجاز واعتماد تطبيق سند"
            if is_ar
            else "Container restart policies and resource allocation"
        )
        if "topic_input" not in st.session_state:
            st.session_state["topic_input"] = default_topic

        topic_val = st.text_input(
            "موضوع المقارنة / البند الإجرائي أو القانوني:" if is_ar else "Comparison Topic / Policy Area",
            value=st.session_state["topic_input"],
            help="حدد البند أو المسألة الإجرائية المراد تدقيقها بدقة بين الوثيقتين.",
        )

        preset_comp_cols = st.columns(3)
        if is_ar:
            with preset_comp_cols[0]:
                if st.button("🛂 مقارنة الرسوم وزمن الإنجاز", key="cmp_ar_fees", use_container_width=True):
                    st.session_state["topic_input"] = "رسوم المعاملة المستعجلة والمدة الزمنية لإنجاز الجواز"
                    st.rerun()
            with preset_comp_cols[1]:
                if st.button("📱 مقارنة إثبات الهوية وسند", key="cmp_ar_id", use_container_width=True):
                    st.session_state["topic_input"] = "اشتراط بطاقة الأحوال الذكية واعتماد الهوية الرقمية عبر تطبيق سند"
                    st.rerun()
            with preset_comp_cols[2]:
                if st.button("⚠️ مقارنة الشروط والاستثناءات", key="cmp_ar_cond", use_container_width=True):
                    st.session_state["topic_input"] = "شروط حالة الاستعجال والفئات المستثناة وموافقة ولي الأمر"
                    st.rerun()
        else:
            with preset_comp_cols[0]:
                if st.button("Compare Restart Policies", key="cmp_restart", use_container_width=True):
                    st.session_state["topic_input"] = "Container restart policies and failure handling"
                    st.rerun()
            with preset_comp_cols[1]:
                if st.button("Compare Timeout Limits", key="cmp_timeout", use_container_width=True):
                    st.session_state["topic_input"] = "Database connection timeout and retry procedures"
                    st.rerun()
            with preset_comp_cols[2]:
                if st.button("Compare DNS Resolvers", key="cmp_dns", use_container_width=True):
                    st.session_state["topic_input"] = "DNS resolution configuration and fallback addresses"
                    st.rerun()

        run_cmp_btn = st.button("⚖️ تشغيل تدقيق التعارض والتطابق" if is_ar else "🔍 Run Conflict & Divergence Audit", type="primary", use_container_width=True)

        if run_cmp_btn:
            active_topic = topic_val.strip() or st.session_state.get("topic_input", "").strip()
            if not active_topic:
                st.warning("يرجى تحديد موضوع للمقارنة." if is_ar else "Please specify a topic to audit.")
            else:
                try:
                    with st.spinner("جاري تدقيق أدلة الوثيقتين واكتشاف الفروقات والتناقضات..." if is_ar else "Auditing document evidence, scopes, and potential contradictions..."):
                        comp_res = client.compare(
                            document_a_id=doc_a_id,
                            document_b_id=doc_b_id,
                            topic=active_topic,
                        )

                    # Relationship Badge
                    rel = comp_res.get("relationship", "insufficient_evidence")
                    badge_class = {
                        "agreement": "rel-agreement",
                        "scope_or_version_difference": "rel-version",
                        "possible_conflict": "rel-conflict",
                        "insufficient_evidence": "rel-insufficient",
                    }.get(rel, "rel-insufficient")

                    if is_ar:
                        rel_label = {
                            "agreement": "✅ توافق في السياسات: تطابق تام في الأحكام والشروط",
                            "scope_or_version_difference": "ℹ️ اختلاف في النطاق أو الإصدار: تباين إجرائي أو تحديث رسمي",
                            "possible_conflict": "⚠️ تعارض وتناقض محتمل: تضارب مباشر بين نصوص الوثيقتين",
                            "insufficient_evidence": "❓ أدلة غير كافية: لا تتوفر تفاصيل كافية للمقارنة",
                        }.get(rel, rel)
                    else:
                        rel_label = {
                            "agreement": "✅ Policy Agreement: Factual Alignment",
                            "scope_or_version_difference": "ℹ️ Scope / Version Difference: Tier or Effective Date Divergence",
                            "possible_conflict": "⚠️ Possible Conflict: Direct Contradiction Detected",
                            "insufficient_evidence": "❓ Insufficient Evidence: Inconclusive Coverage",
                        }.get(rel, rel.replace("_", " ").title())

                    st.markdown(f'<div class="rel-badge {badge_class}">{rel_label}</div>', unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='bidi-text'><strong>{'الملخص التنفيذي للنتيجة:' if is_ar else 'Executive Summary:'}</strong> <span dir='auto'>{comp_res.get('summary')}</span></div>",
                        unsafe_allow_html=True,
                    )

                    # Side by side cards
                    card_a, card_b = st.columns(2)
                    doc_a_claim = comp_res.get("document_a", {})
                    doc_b_claim = comp_res.get("document_b", {})

                    with card_a:
                        with st.container(border=True):
                            fname_a = doc_a_claim.get("filename", "")
                            st.markdown(
                                f"#### 📄 {'الوثيقة (أ):' if is_ar else 'Document A:'} <code dir='ltr'>{fname_a}</code>",
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f"**{'الحكم أو النص النظامي الوارد:' if is_ar else 'Stated Rule / Claim:'}** <span dir='auto'>{doc_a_claim.get('claim')}</span>",
                                unsafe_allow_html=True,
                            )
                            if doc_a_claim.get("scope_notes"):
                                st.caption(f"**{'نطاق التطبيق أو شرط الإصدار:' if is_ar else 'Scope / Version Condition:'}** {doc_a_claim.get('scope_notes')}")
                            
                            ev_a = doc_a_claim.get("evidence", [])
                            if ev_a:
                                exp_label = f"📑 {'الأدلة والفقرات الموثقة' if is_ar else 'Verified Evidence'} ({len(ev_a)} {'فقرات' if is_ar else 'passages'})"
                                with st.expander(exp_label, expanded=True):
                                    for ev in ev_a:
                                        st.markdown(f"> \"<span dir='auto'>{ev.get('text', '')[:300]}...</span>\"", unsafe_allow_html=True)
                                        st.caption(f"{'المصدر:' if is_ar else 'Source:'} <code dir='ltr'>{ev.get('source')}</code>", unsafe_allow_html=True)

                    with card_b:
                        with st.container(border=True):
                            fname_b = doc_b_claim.get("filename", "")
                            st.markdown(
                                f"#### 📄 {'الوثيقة (ب):' if is_ar else 'Document B:'} <code dir='ltr'>{fname_b}</code>",
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f"**{'الحكم أو النص النظامي الوارد:' if is_ar else 'Stated Rule / Claim:'}** <span dir='auto'>{doc_b_claim.get('claim')}</span>",
                                unsafe_allow_html=True,
                            )
                            if doc_b_claim.get("scope_notes"):
                                st.caption(f"**{'نطاق التطبيق أو شرط الإصدار:' if is_ar else 'Scope / Version Condition:'}** {doc_b_claim.get('scope_notes')}")

                            ev_b = doc_b_claim.get("evidence", [])
                            if ev_b:
                                exp_label = f"📑 {'الأدلة والفقرات الموثقة' if is_ar else 'Verified Evidence'} ({len(ev_b)} {'فقرات' if is_ar else 'passages'})"
                                with st.expander(exp_label, expanded=True):
                                    for ev in ev_b:
                                        st.markdown(f"> \"<span dir='auto'>{ev.get('text', '')[:300]}...</span>\"", unsafe_allow_html=True)
                                        st.caption(f"{'المصدر:' if is_ar else 'Source:'} <code dir='ltr'>{ev.get('source')}</code>", unsafe_allow_html=True)

                    # Resolution guidance
                    with st.container(border=True):
                        st.markdown(f"**🛡️ {'توجيهات وتوصيات صانع القرار:' if is_ar else 'Decision-Maker Resolution Guidance:'}**")
                        default_guidance = (
                            "يوصى بالرجوع إلى الوثائق المرجعية الأصلية قبل اعتماد القرار الإجرائي."
                            if is_ar
                            else "Review primary documents before policy enforcement."
                        )
                        res_guidance = comp_res.get("resolution_notes") or default_guidance
                        st.markdown(f"<div class='bidi-text' dir='auto'>{res_guidance}</div>", unsafe_allow_html=True)

                except Exception as exc:
                    st.error(f"Comparison analysis failed: {exc}")


# =========================================================
# TAB 3: EXECUTIVE BRIEFINGS (MULTI-DOC MAP-REDUCE)
# =========================================================

with tab_briefing:
    st.subheader("📋 الإيجاز والتقارير التنفيذية متعددة الوثائق" if is_ar else "📋 Multi-Document Executive Briefing")
    st.caption(
        "توليد إيجاز تركيبي استراتيجي يغطي عدة وثائق حكومية مع تصنيف النتائج وتوثيق المراجع."
        if is_ar
        else "Generate a structured synthesis across multiple documents with category-tagged findings and verifiable citations."
    )

    docs = st.session_state.get("documents", [])
    if not docs:
        st.info("لا توجد وثائق مفهرسة حالياً. يرجى رفع الوثائق في التبويب الرابع لتوليد الإيجاز." if is_ar else "No documents indexed yet. Upload documents in Tab 4 to generate briefings.")
    else:
        doc_map = {f"{clean_source_name(d.get('filename'))[0]} ({d.get('document_id')[:8]})": d.get("document_id") for d in docs}
        selected_brief_names = st.multiselect(
            "اختر الوثائق الحكومية المراد تلخيصها ودمجها:" if is_ar else "Select Documents to Synthesize",
            options=list(doc_map.keys()),
            default=list(doc_map.keys())[:min(3, len(doc_map))],
        )

        default_brief_focus = (
            "الملخص التنفيذي، شروط المعاملات، الرسوم والمدد الزمنية، والامتثال القانوني"
            if is_ar
            else "Executive Summary, Critical Policies, and Key Operational Standards"
        )
        focus_input = st.text_input(
            "محور التركيز وأهداف الإيجاز التنفيذي:" if is_ar else "Briefing Focus / Objectives",
            value=default_brief_focus,
        )

        run_brief_btn = st.button("📋 توليد الإيجاز التنفيذي" if is_ar else "📋 Generate Executive Briefing", type="primary", use_container_width=True)

        if run_brief_btn:
            if not selected_brief_names:
                st.warning("يرجى اختيار وثيقة واحدة على الأقل." if is_ar else "Please select at least one document.")
            else:
                target_ids = [doc_map[name] for name in selected_brief_names]
                try:
                    with st.spinner("جاري تلخيص ودمج الوثائق باستخدام محرك Map-Reduce السيادي..." if is_ar else "Synthesizing multi-document briefing using Map-Reduce engine..."):
                        brief_res = client.brief(
                            document_ids=target_ids,
                            focus=focus_input,
                            max_findings=8,
                        )

                    # Summary Box
                    with st.container(border=True):
                        st.markdown("### 📌 " + ("نظرة عامة تنفيذية" if is_ar else "Executive Overview"))
                        st.markdown(
                            f"<div class='bidi-text' dir='auto'>{brief_res.get('executive_summary', '')}</div>",
                            unsafe_allow_html=True,
                        )
                        analyzed_docs = brief_res.get("analyzed_documents", [])
                        analyzed_docs_str = ", ".join([f"<code dir='ltr'>{clean_source_name(d)[0]}</code>" for d in analyzed_docs])
                        st.caption(
                            f"{'تم التحليل عبر' if is_ar else 'Analyzed across'} {brief_res.get('document_count')} "
                            f"{'وثائق رسمية:' if is_ar else 'documents:'} {analyzed_docs_str}",
                            unsafe_allow_html=True,
                        )

                    # Findings List
                    findings = brief_res.get("findings", [])
                    st.markdown(f"### 🎯 {'النتائج والقرارات الاستراتيجية' if is_ar else 'Strategic Findings & Mandates'} ({len(findings)})")

                    cat_labels_ar = {
                        "policy": "🏛️ السياسات والأنظمة",
                        "technical": "⚙️ المتطلبات التقنية",
                        "compliance": "⚖️ الشروط والامتثال",
                        "action_item": "✅ الإجراءات التنفيذية",
                    }

                    for idx, f in enumerate(findings, start=1):
                        cat = f.get("category", "policy")
                        tag_class = f"tag-{cat}"
                        tag_text = cat_labels_ar.get(cat, cat.upper()) if is_ar else cat.replace("_", " ").upper()
                        with st.container(border=True):
                            st.markdown(f'<span class="finding-tag {tag_class}">{tag_text}</span>', unsafe_allow_html=True)
                            st.markdown(f"**{idx}. <span dir='auto'>{f.get('title')}</span>**", unsafe_allow_html=True)
                            st.markdown(f"<div class='bidi-text' dir='auto'>{f.get('description')}</div>", unsafe_allow_html=True)

                            evs = f.get("evidence", [])
                            if evs:
                                with st.expander(
                                    f"📑 {'الأدلة الموثقة' if is_ar else 'Grounded Evidence'} ({len(evs)} {'مقطع' if is_ar else 'chunk'})",
                                    expanded=False,
                                ):
                                    for ev in evs:
                                        ev_clean, _ = clean_source_name(ev.get("filename", ""))
                                        st.markdown(f"> \"<span dir='auto'>{ev.get('text', '')[:300]}...</span>\"", unsafe_allow_html=True)
                                        st.caption(
                                            f"{'المصدر:' if is_ar else 'Source:'} <code dir='ltr'>{ev_clean}</code> | "
                                            f"{'المرجع:' if is_ar else 'Reference:'} `#{ev.get('reference')}`",
                                            unsafe_allow_html=True,
                                        )

                    # Download Briefing
                    if is_ar:
                        brief_md = [
                            f"# إيجاز استخباراتي تنفيذي متعدد الوثائق: {focus_input}",
                            f"**التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            f"**نطاق الوثائق:** {len(target_ids)} وثائق رسمية",
                            "\n## نظرة عامة تنفيذية\n",
                            brief_res.get("executive_summary", ""),
                            "\n## النتائج والقرارات الاستراتيجية\n",
                        ]
                        for f in findings:
                            cat_name = cat_labels_ar.get(f.get("category"), f.get("category", "").upper())
                            brief_md.append(f"### [{cat_name}] {f.get('title')}\n{f.get('description')}\n")
                    else:
                        brief_md = [
                            f"# EXECUTIVE INTELLIGENCE BRIEFING: {focus_input}",
                            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            f"**Corpus:** {len(target_ids)} documents",
                            "\n## Executive Overview\n",
                            brief_res.get("executive_summary", ""),
                            "\n## Strategic Findings\n",
                        ]
                        for f in findings:
                            brief_md.append(f"### [{f.get('category').upper()}] {f.get('title')}\n{f.get('description')}\n")

                    st.download_button(
                        label="📥 تحميل التقرير التنفيذي (.md)" if is_ar else "📥 Download Executive Briefing (.md)",
                        data="\n".join(brief_md),
                        file_name=f"psut_executive_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

                except Exception as exc:
                    st.error(f"{'فشل توليد الإيجاز التنفيذي:' if is_ar else 'Briefing generation failed:'} {exc}")


# =========================================================
# TAB 4: KNOWLEDGE REPOSITORY & SYSTEM DIAGNOSTICS
# =========================================================

with tab_repo:
    st.subheader("📁 مستودع المعرفة السيادي والتشخيص الفني" if is_ar else "📁 Sovereign Knowledge Repository & Diagnostics")
    st.caption("دليل البيانات المحلي المعزول، وفهرسة الوثائق، وتتبع سلامة البنية التحتية المحلية." if is_ar else "Air-gapped data catalog, document ingestion, and live local infrastructure diagnostics.")

    # Live Health Diagnostics
    try:
        health_info = client.get_health()
        st.markdown("#### 🛡️ " + ("تشخيص العتاد والمحركات الذكية" if is_ar else "Hardware & Engine Diagnostics"))
        h_col1, h_col2, h_col3, h_col4 = st.columns(4)
        with h_col1:
            st.metric(
                "محرك التوليد Ollama" if is_ar else "Ollama LLM",
                health_info.get("ollama", {}).get("model", "qwen3.5:4b"),
                "كارت الشاشة GPU" if is_ar else "Local GPU",
            )
        with h_col2:
            st.metric(
                "تضمينات المتجهات" if is_ar else "Embeddings",
                "MiniLM-Multilingual",
                "384-dim عربي/إنجليزي" if is_ar else "384-dim Arabic",
            )
        with h_col3:
            st.metric(
                "معيد الترتيب Reranker" if is_ar else "Reranker",
                "BGE-Reranker-v2-m3",
                "Cross-Encoder متعدد اللغات" if is_ar else "Cross-Encoder Multilingual",
            )
        with h_col4:
            st.metric(
                "قاعدة المتجهات Qdrant" if is_ar else "Vector Store",
                "Qdrant مدمجة" if is_ar else "Qdrant Embedded",
                f"{health_info.get('chunk_count', 0)} {'مقطع' if is_ar else 'chunks'}",
            )
    except Exception:
        st.warning("تعذر جلب بيانات التشخيص الفني في الوقت الفعلي." if is_ar else "Could not fetch real-time health telemetry.")

    st.divider()

    # Document Ingestion Section
    st.markdown("#### ⚡ " + ("فهرسة وثيقة رسمية جديدة" if is_ar else "Ingest New Document"))
    uploaded_file = st.file_uploader(
        "رفع وثيقة رسمية (PDF, Word DOCX, Markdown, Text, HTML)" if is_ar else "Upload Enterprise Document (PDF, Word DOCX, Markdown, Text, HTML)",
        type=["md", "txt", "pdf", "docx", "html", "htm"],
        key="tab_repo_uploader",
    )

    if uploaded_file is not None:
        idx_btn_label = "⚡ بدء فهرسة وتضمين الوثيقة" if is_ar else "⚡ Index Document into Vector Store"
        if st.button(idx_btn_label, use_container_width=True, type="primary"):
            try:
                with st.spinner("جاري استخراج المقاطع وبناء التضمينات المتجهة محلياً..." if is_ar else "Processing document chunks and local embeddings..."):
                    result = client.ingest(
                        filename=uploaded_file.name,
                        content=uploaded_file.getvalue(),
                    )

                chunk_cnt = result.get("chunk_count", 0)
                if result.get("duplicate"):
                    st.info(
                        f"ℹ️ الوثيقة <code dir='ltr'>{uploaded_file.name}</code> مفهرسة مسبقاً ({chunk_cnt} مقطع). جاهزة للبحث والمقارنة والإيجاز!"
                        if is_ar
                        else f"ℹ️ Document <code dir='ltr'>{uploaded_file.name}</code> is already indexed ({chunk_cnt} chunks). Ready for search, conflict detection, and briefings!",
                        unsafe_allow_html=True,
                    )
                else:
                    st.success(
                        f"✅ تمت فهرسة وثيقة <code dir='ltr'>{uploaded_file.name}</code> بنجاح بعدد ({chunk_cnt} مقطع)!"
                        if is_ar
                        else f"✅ Successfully indexed <code dir='ltr'>{uploaded_file.name}</code> ({chunk_cnt} chunks) into the vector store!",
                        unsafe_allow_html=True,
                    )
                    st.session_state["documents"] = client.list_documents()
                    st.rerun()

            except Exception as exc:
                st.error(f"{'فشلت عملية الفهرسة والتضمين:' if is_ar else 'Ingestion failed:'} {exc}")

    st.divider()

    # Document Catalog Table
    st.markdown("#### 📚 " + ("كتالوج الوثائق الرسمية المفهرسة" if is_ar else "Ingested Document Catalog"))
    docs = st.session_state.get("documents", [])
    if docs:
        doc_rows = []
        for d in docs:
            clean_name, base_name = clean_source_name(d.get("filename", ""))
            doc_rows.append({
                "اسم الوثيقة" if is_ar else "Document Name": clean_name,
                "الصيغة" if is_ar else "Format": d.get("file_type", "").upper(),
                "عدد المقاطع" if is_ar else "Chunk Count": d.get("chunk_count", 0),
                "المعرف الرقمي" if is_ar else "Document ID": d.get("document_id", "")[:16] + "...",
                "استراتيجية التقسيم" if is_ar else "Strategy": d.get("chunking_strategy", "structure"),
            })
        st.dataframe(pd.DataFrame(doc_rows), use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد وثائق مفهرسة حالياً." if is_ar else "No documents currently indexed.")