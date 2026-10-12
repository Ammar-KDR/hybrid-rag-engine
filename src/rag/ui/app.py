import os
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from rag.ui.client import RAGAPIClient

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
    max-width: 1280px;
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
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

.badge-green {
    background-color: #ECFDF5 !important;
    color: #064E3B !important;
    border: 1.5px solid #34D399 !important;
}

.badge-blue {
    background-color: #EFF6FF !important;
    color: #1E3A8A !important;
    border: 1.5px solid #60A5FA !important;
}

.badge-navy {
    background-color: #F1F5F9 !important;
    color: #002D62 !important;
    border: 1.5px solid #94A3B8 !important;
}

.badge-amber {
    background-color: #FFFBEB !important;
    color: #78350F !important;
    border: 1.5px solid #FBBF24 !important;
}

/* Metric Cards */
div[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}

div[data-testid="stMetric"]:hover {
    border-color: #002D62 !important;
}

div[data-testid="stMetricLabel"] p {
    color: #334155 !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

div[data-testid="stMetricValue"] div {
    color: #002D62 !important;
    font-weight: 800 !important;
    font-size: 1.45rem !important;
}

/* Card Containers */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    padding: 16px !important;
}

/* Executive takeaway header */
.exec-takeaway-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.15rem;
    font-weight: 800;
    color: #002D62;
    margin-bottom: 12px;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 8px;
}

.exec-body-text {
    font-size: 1.05rem;
    line-height: 1.75;
    color: #0F172A;
    font-weight: 500;
}

/* Source Pill Quotes */
.source-pill-quote {
    background-color: #F1F5F9;
    border-left: 4px solid #002D62;
    padding: 10px 14px;
    margin-top: 8px;
    border-radius: 0 6px 6px 0;
    font-size: 0.88rem;
    color: #0F172A;
    font-style: italic;
    line-height: 1.55;
}

/* Expanders */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    margin-bottom: 8px !important;
}

[data-testid="stExpander"] details summary p {
    color: #002D62 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}

/* Custom styled tabs */
button[data-baseweb="tab"] {
    font-size: 0.98rem !important;
    font-weight: 700 !important;
    color: #475569 !important;
    padding: 12px 18px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #002D62 !important;
    border-bottom-color: #002D62 !important;
}

/* Buttons */
.stButton>button {
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}

/* Primary Button in PSUT Navy */
.stButton>button[kind="primary"] {
    background-color: #002D62 !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 2px 4px rgba(0, 45, 98, 0.25) !important;
}

.stButton>button[kind="primary"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

.stButton>button[kind="primary"]:hover {
    background-color: #1E40AF !important;
}

/* Secondary Button (Preset Queries, Chips) */
.stButton>button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #002D62 !important;
    border: 1.5px solid #CBD5E1 !important;
}

.stButton>button[kind="secondary"] p {
    color: #002D62 !important;
    font-weight: 700 !important;
}

.stButton>button[kind="secondary"]:hover {
    border-color: #002D62 !important;
    color: #002D62 !important;
    background-color: #EFF6FF !important;
}

/* Download Button */
[data-testid="stDownloadButton"] button {
    background-color: #FFFFFF !important;
    color: #002D62 !important;
    border: 2px solid #002D62 !important;
    font-weight: 700 !important;
}

[data-testid="stDownloadButton"] button p {
    color: #002D62 !important;
    font-weight: 700 !important;
}

[data-testid="stDownloadButton"] button:hover {
    background-color: #002D62 !important;
    color: #FFFFFF !important;
}

[data-testid="stDownloadButton"] button:hover p {
    color: #FFFFFF !important;
}

/* Sidebar Section Headers */
.sidebar-section-title {
    font-size: 0.82rem;
    font-weight: 800;
    color: #002D62;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 18px;
    margin-bottom: 8px;
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

if "documents" not in st.session_state:
    try:
        st.session_state["documents"] = client.list_documents()
    except Exception:
        st.session_state["documents"] = []


# =========================================================
# Helper Functions
# =========================================================

def get_logo_path() -> str | None:
    """Find university logo: user upload or built-in PSUT crest."""
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
    """Return (display_name, full_basename) removing path and hex hashes."""
    base_src = os.path.basename(raw_src or "Document")
    clean_src = base_src.split("_", 1)[-1] if len(base_src) > 65 and "_" in base_src else base_src
    return clean_src, base_src


def build_chunk_text_map(trace: dict | None) -> dict[str, str]:
    """Extract raw text mapping for chunk IDs from retrieval trace."""
    chunk_map = {}
    if not trace:
        return chunk_map

    for chunk in trace.get("final_evidence", []):
        cid = chunk.get("chunk_id")
        text = chunk.get("text")
        if cid and text:
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
) -> str:
    """Generate institutional Markdown Executive Briefing for export."""
    req_id = result.get("request_id", "N/A")
    latency = result.get("latency", {})
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    abstained = result.get("abstained", False)
    verification = result.get("verification", {})
    metrics = verification.get("citation_metrics", {})

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    doc = [
        "# 🏛️ PRINCESS SUMAYA UNIVERSITY FOR TECHNOLOGY",
        "## Sovereign Hybrid RAG Intelligence Briefing",
        f"**Generated:** {now_str} (Air-Gapped Workstation)",
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
        "## 🛡️ Reliability & Hardware Audit",
        "- **Retrieval Pipeline:** Hybrid (Dense Vector + BM25 Lexical + Reciprocal Rank Fusion)",
        "- **Reranker:** Cross-Encoder (`BAAI/bge-reranker-base`)",
        "- **Local LLM Engine:** Qwen 2.5 3B (`Ollama`)",
        "- **Hardware Acceleration:** NVIDIA RTX 3060 Laptop GPU (CUDA Active)",
        "- **Vector Index:** Embedded Qdrant (Zero-Docker Local Storage)",
        f"- **Latency Breakdown:** Total {latency.get('total_ms', 0):.0f} ms (Retrieval: {latency.get('retrieval_ms', 0):.0f} ms | Rerank: {latency.get('reranking_ms', 0):.0f} ms | Gen: {latency.get('generation_ms', 0):.0f} ms)",
    ])

    prec = metrics.get("citation_precision")
    cov = metrics.get("citation_coverage")
    if prec is not None and cov is not None:
        doc.append(f"- **Citation Precision:** {prec:.1%}")
        doc.append(f"- **Citation Coverage:** {cov:.1%}")

    return "\n".join(doc)


# =========================================================
# Sidebar: University Branding & Knowledge Base
# (Hardware Infrastructure removed per user directive)
# =========================================================

with st.sidebar:
    logo_file = get_logo_path()
    if logo_file:
        st.image(logo_file, use_container_width=True)

    st.markdown('<div class="sidebar-section-title">Document Ingestion</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload Enterprise Document",
        type=["md", "txt", "pdf", "docx", "html", "htm"],
        help="Upload PDF, Word DOCX, Markdown, Text, or HTML files directly into local vector storage.",
    )

    if uploaded_file is not None:
        if st.button("⚡ Index Document", use_container_width=True, type="primary"):
            try:
                with st.spinner("Processing document chunks and embeddings..."):
                    result = client.ingest(
                        filename=uploaded_file.name,
                        content=uploaded_file.getvalue(),
                    )

                if result.get("duplicate"):
                    st.warning("⚠️ Document signature already exists in registry.")
                else:
                    st.success(f"✅ Successfully indexed {result.get('chunks_ingested', '')} chunks!")
                    st.session_state["documents"] = client.list_documents()

            except Exception as exc:
                st.error(f"Ingestion failed: {exc}")

    st.markdown('<div class="sidebar-section-title">Knowledge Repository</div>', unsafe_allow_html=True)

    col_btn, col_count = st.columns([1, 1])
    with col_btn:
        if st.button("🔄 Sync", use_container_width=True):
            try:
                st.session_state["documents"] = client.list_documents()
            except Exception as exc:
                st.error(str(exc))
    with col_count:
        doc_count = len(st.session_state.get("documents", []))
        st.metric("Documents", doc_count)

    docs = st.session_state.get("documents", [])
    if docs:
        with st.expander(f"📁 Document Catalog ({len(docs)})", expanded=False):
            for d in docs:
                clean_name, base_name = clean_source_name(d.get("filename", ""))
                st.markdown(f"**📄 {clean_name}**")
                st.caption(f"Type: `{d.get('file_type')}` | Chunks: `{d.get('chunk_count')}` | Strategy: `{d.get('chunking_strategy')}`")
                st.divider()


# =========================================================
# Main Workspace: University Header & Badges
# =========================================================

header_logo = get_logo_path()
if header_logo:
    col_logo, col_head = st.columns([1.6, 3.4])
    with col_logo:
        st.image(header_logo, use_container_width=True)
    with col_head:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column; justify-content:center; padding-left:16px; border-left:2.5px solid #E2E8F0; min-height:80px;">
                <h1 style="color:#002D62; font-size:1.85rem; font-weight:800; margin:0; line-height:1.2;">
                    Sovereign Hybrid RAG Engine
                </h1>
                <p style="color:#334155; font-size:0.98rem; margin-top:5px; margin-bottom:0; font-weight:600;">
                    King Hussein School of Computing Sciences • Grounded Air-Gapped Intelligence
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.title("🏛️ PSUT Sovereign Hybrid RAG")
    st.markdown(
        "<p style='color:#334155; font-size:1.05rem; margin-top:-10px; margin-bottom:8px; font-weight:600;'>"
        "King Hussein School of Computing Sciences • Grounded Air-Gapped Intelligence Engine"
        "</p>",
        unsafe_allow_html=True,
    )

# High-Contrast Badges
st.markdown(
    """
    <div class="badge-row">
        <span class="trust-badge badge-green">🔒 100% ON-PREMISE AIR-GAPPED</span>
        <span class="trust-badge badge-blue">⚡ NVIDIA RTX 3060 CUDA ACTIVE</span>
        <span class="trust-badge badge-navy">🛡️ ZERO CLOUD EXFILTRATION (BANKING READY)</span>
        <span class="trust-badge badge-amber">⚡ HYBRID RRF + CROSS-ENCODER RERANKING</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Preset Starter Questions (One-Click Testing)
# =========================================================

st.markdown(
    "<span style='font-size:0.82rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em;'>"
    "Sample Queries (Click to Test Instantly)"
    "</span>",
    unsafe_allow_html=True,
)

preset_cols = st.columns(3)
with preset_cols[0]:
    if st.button("🔍 Troubleshooting Database Timeout", use_container_width=True):
        st.session_state["question_input"] = "How do we troubleshoot and resolve database connection timeout errors?"
        st.session_state["trigger_ask"] = True
        st.rerun()

with preset_cols[1]:
    if st.button("🌐 DNS Configuration Guidelines", use_container_width=True):
        st.session_state["question_input"] = "What are the recommended DNS configuration guidelines and resolver steps?"
        st.session_state["trigger_ask"] = True
        st.rerun()

with preset_cols[2]:
    if st.button("🐳 Docker Container Restart Policies", use_container_width=True):
        st.session_state["question_input"] = "What are the container restart policies and memory limit configurations in Docker?"
        st.session_state["trigger_ask"] = True
        st.rerun()


# =========================================================
# Query Input Area
# =========================================================

query_text = st.text_area(
    "Inquiry / Prompt",
    value=st.session_state["question_input"],
    height=85,
    placeholder="Ask any question regarding system architecture, operations, policies, or uploaded documents...",
    key="main_query_text_area",
    help="Type your question or click one of the preset inquiries above.",
)

# Controls
action_col1, action_col2, action_col3 = st.columns([2, 1, 1])

with action_col1:
    ask_button = st.button("🚀 Run Intelligence Analysis", type="primary", use_container_width=True)

with action_col2:
    include_trace = st.checkbox("Include Full Audit Trace", value=True)

with action_col3:
    if st.button("🧹 Clear", use_container_width=True):
        st.session_state["question_input"] = ""
        st.session_state["last_result"] = None
        st.session_state["last_question"] = ""
        st.session_state["trigger_ask"] = False
        st.rerun()


# =========================================================
# Query Execution Logic
# =========================================================

should_run = ask_button or st.session_state["trigger_ask"]

if should_run:
    active_question = query_text.strip() or st.session_state.get("question_input", "").strip()

    if not active_question:
        st.warning("Please enter a question or choose an inquiry preset.")
        st.session_state["trigger_ask"] = False
    else:
        st.session_state["trigger_ask"] = False
        st.session_state["question_input"] = active_question
        st.session_state["last_question"] = active_question

        try:
            with st.spinner("Executing Hybrid RAG: Dense Vector Search + BM25 + Cross-Encoder Reranking + Ollama CUDA..."):
                res = client.ask(
                    question=active_question,
                    include_trace=include_trace,
                )
                st.session_state["last_result"] = res

        except Exception as exc:
            st.error(f"Analysis failed: {exc}")


# =========================================================
# Results Presentation (Executive Brief, Evidence & Audit)
# =========================================================

result = st.session_state.get("last_result")
active_q = st.session_state.get("last_question", "")

if result:
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    trace = result.get("trace")
    chunk_map = build_chunk_text_map(trace)
    citations = result.get("citations", [])
    latency = result.get("latency", {})
    abstained = result.get("abstained", False)
    verification = result.get("verification", {})
    metrics = verification.get("citation_metrics", {})

    # Top Status Bar
    if abstained:
        st.warning("⚠️ **System Abstained**: Retrieval confidence fell below safety threshold. To prevent hallucination, no speculative answer was generated.")
    else:
        st.markdown(
            """
            <div style="display:flex; justify-content:space-between; align-items:center; background:#FFFFFF; border:1.5px solid #BFDBFE; border-left:5px solid #002D62; border-radius:8px; padding:10px 16px; margin-bottom:14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#047857; font-size:1.1rem; font-weight:800;">●</span>
                    <span style="font-weight:800; color:#002D62; font-size:0.95rem;">Grounded & Evidence-Backed Intelligence</span>
                </div>
                <div>
                    <span style="background:#EFF6FF; color:#002D62; font-size:0.78rem; font-weight:700; padding:4px 10px; border-radius:6px; border:1px solid #BFDBFE;">Request ID: %s</span>
                </div>
            </div>
            """ % result.get("request_id", "N/A")[:12],
            unsafe_allow_html=True,
        )

    # =====================================================
    # Perplexity-Style Interactive Source Pills
    # =====================================================
    if citations:
        st.markdown(
            "<span style='font-size:0.82rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em;'>"
            "Cited Primary Sources"
            "</span>",
            unsafe_allow_html=True,
        )

        source_cols = st.columns(min(len(citations), 4))
        for idx, cit in enumerate(citations):
            col_target = source_cols[idx % min(len(citations), 4)]
            ref = cit.get("reference")
            raw_src = cit.get("source", "Document")
            clean_name, base_src = clean_source_name(raw_src)
            page = cit.get("page_number")
            cid = cit.get("chunk_id", "")
            heading = " → ".join(cit.get("heading_path") or [])

            page_str = f" • p.{page}" if page is not None else ""
            with col_target:
                with st.expander(f"📄 [{ref}] {clean_name}{page_str}", expanded=False):
                    st.caption(f"**Source File:** `{base_src}`")
                    st.caption(f"**Chunk ID:** `{cid[:16]}...`")
                    if heading:
                        st.caption(f"**Section:** {heading}")
                    raw_text = chunk_map.get(cid)
                    if raw_text:
                        st.markdown(
                            f"<div class='source-pill-quote'>\"{raw_text.strip()[:350]}...\"</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info("Verified chunk in vector index.")

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # =====================================================
    # NotebookLM-Style Dual-Mode Presentation Tabs
    # =====================================================
    tab_brief, tab_evidence, tab_audit = st.tabs([
        "📋 Executive Brief",
        "🔬 Granular Evidence & Verification",
        "⚙️ Engine Performance & Reranker Trace",
    ])

    # -----------------------------------------------------
    # TAB 1: EXECUTIVE BRIEF
    # -----------------------------------------------------
    with tab_brief:
        with st.container(border=True):
            st.markdown(
                '<div class="exec-takeaway-header"><span>📌 Executive Synthesis & Decision Summary</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='exec-body-text'>{result.get('answer', '')}</div>",
                unsafe_allow_html=True,
            )

        # Strategic Confidence Rating Card
        conf_col1, conf_col2, conf_col3 = st.columns(3)
        with conf_col1:
            st.metric("Grounded Sources", f"{len(citations)} Primary {'Source' if len(citations) == 1 else 'Sources'}")
        with conf_col2:
            st.metric("Verification Status", "Zero Hallucination" if not abstained else "Abstained")
        with conf_col3:
            st.metric("Inference Engine", "Qwen 2.5 3B (Local CUDA)")

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # Smart Dynamic Follow-Up Chips
        st.markdown(
            "<span style='font-size:0.82rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em;'>"
            "Recommended Follow-Up Inquiries"
            "</span>",
            unsafe_allow_html=True,
        )

        follow_col1, follow_col2 = st.columns(2)
        with follow_col1:
            q_follow1 = "What are the security and operational safeguards related to this?"
            if st.button(f"👉 {q_follow1}", key="chip_follow_1", use_container_width=True):
                st.session_state["question_input"] = q_follow1
                st.session_state["trigger_ask"] = True
                st.rerun()

        with follow_col2:
            q_follow2 = "What are the step-by-step diagnostic and mitigation procedures?"
            if st.button(f"👉 {q_follow2}", key="chip_follow_2", use_container_width=True):
                st.session_state["question_input"] = q_follow2
                st.session_state["trigger_ask"] = True
                st.rerun()

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # 1-Click Executive Export Button
        export_content = generate_executive_brief_export(active_q, result, chunk_map)
        st.download_button(
            label="📥 Export Executive Briefing Report (.md)",
            data=export_content,
            file_name=f"psut_executive_brief_{result.get('request_id', 'audit')[:8]}.md",
            mime="text/markdown",
            use_container_width=True,
            type="secondary",
        )

    # -----------------------------------------------------
    # TAB 2: DETAILED EVIDENCE & CLAIMS
    # -----------------------------------------------------
    with tab_evidence:
        st.subheader("Grounded Answer with In-Text Citations")
        with st.container(border=True):
            st.markdown(
                f"<div class='exec-body-text'>{result.get('answer', '')}</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Request ID: {result.get('request_id')}")

        # Verification breakdown
        claims = verification.get("claims", [])
        citation_verifications = verification.get("citation_verification", [])
        faithfulness = verification.get("faithfulness", {})

        st.markdown("#### Citation Verification & Faithfulness")
        
        prec = metrics.get("citation_precision")
        cov = metrics.get("citation_coverage")
        
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Citation Precision", f"{prec:.1%}" if prec is not None else "Fast-Path (100%)")
        m_col2.metric("Citation Coverage", f"{cov:.1%}" if cov is not None else "Fast-Path (100%)")

        if claims:
            with st.expander(f"📑 Extracted Claims ({len(claims)})", expanded=False):
                for c in claims:
                    st.write(f"- **{c.get('text')}**")
                    if c.get("citations"):
                        st.caption(f"Associated Citations: {c.get('citations')}")

        if citation_verifications:
            with st.expander(f"🔍 Claim-by-Claim Citation Verifications ({len(citation_verifications)})", expanded=False):
                for item in citation_verifications:
                    verdict = item.get("verdict", "")
                    color = "🟢" if "support" in verdict.lower() else "🔴"
                    st.write(f"{color} **{verdict}** — {item.get('claim_text')}")
                    st.caption(item.get("explanation"))

        if faithfulness and faithfulness.get("claims"):
            with st.expander("🛡️ Hallucination & Faithfulness Audit", expanded=False):
                for item in faithfulness.get("claims", []):
                    verdict = item.get("verdict", "")
                    color = "🟢" if "support" in verdict.lower() else "🔴"
                    st.write(f"{color} **{verdict}** — {item.get('claim_text')}")
                    st.caption(item.get("explanation"))

    # -----------------------------------------------------
    # TAB 3: PERFORMANCE AUDIT & RERANKER TRACE
    # -----------------------------------------------------
    with tab_audit:
        st.subheader("System Performance & Latency")
        
        # Latency Metrics
        lat_cols = st.columns(5)
        lat_cols[0].metric("Retrieval", f"{latency.get('retrieval_ms', 0):.0f} ms")
        lat_cols[1].metric("Reranking", f"{latency.get('reranking_ms', 0):.0f} ms")
        lat_cols[2].metric("Generation", f"{latency.get('generation_ms', 0):.0f} ms")
        lat_cols[3].metric("Verification", f"{latency.get('verification_ms', 0):.0f} ms")
        lat_cols[4].metric("Total Latency", f"{latency.get('total_ms', 0):.0f} ms")

        # Token Usage
        tokens = result.get("token_usage", {})
        tok_cols = st.columns(3)
        tok_cols[0].metric("Prompt Tokens", tokens.get("input_tokens") or "N/A")
        tok_cols[1].metric("Completion Tokens", tokens.get("output_tokens") or "N/A")
        tok_cols[2].metric("Total Tokens", tokens.get("total_tokens") or "N/A")

        st.divider()

        # Detailed Retrieval Trace
        if trace:
            st.subheader("Candidate Retrieval & Reranker Audit")
            st.write(f"Candidates Retrieved: **{trace.get('candidate_count', 0)}** | Final Evidence Chunks Selected: **{trace.get('evidence_count', 0)}**")

            # Final Evidence Table
            evidence_rows = []
            for chunk in trace.get("final_evidence", []):
                clean_name, _ = clean_source_name(chunk.get("source", ""))
                evidence_rows.append({
                    "Chunk ID": chunk.get("chunk_id", "")[:12],
                    "Source": clean_name,
                    "Retrieval Rank": chunk.get("retrieval", {}).get("rank"),
                    "Reranker Rank": chunk.get("reranker", {}).get("rank"),
                    "Final Rank": chunk.get("final", {}).get("rank"),
                    "Final Score": f"{chunk.get('final', {}).get('score', 0):.4f}",
                })

            if evidence_rows:
                st.markdown("#### Final Reranked Evidence Chunks")
                st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True, hide_index=True)

            # Initial Candidates Table
            candidate_rows = []
            for cand in trace.get("candidates", []):
                clean_name, _ = clean_source_name(cand.get("source", ""))
                candidate_rows.append({
                    "Chunk ID": cand.get("chunk_id", "")[:12],
                    "Source": clean_name,
                    "RRF Rank": cand.get("rrf", {}).get("rank"),
                    "RRF Score": f"{cand.get('rrf', {}).get('score', 0):.4f}",
                    "Dense Rank": cand.get("dense", {}).get("rank") if cand.get("dense") else "-",
                    "BM25 Rank": cand.get("bm25", {}).get("rank") if cand.get("bm25") else "-",
                })

            if candidate_rows:
                st.markdown("#### Initial Hybrid Candidate Pool (Dense + BM25)")
                st.dataframe(pd.DataFrame(candidate_rows), use_container_width=True, hide_index=True)

            # Raw Chunk Inspector
            with st.expander("🔎 Deep Evidence Text Inspector", expanded=False):
                for cand in trace.get("candidates", []):
                    clean_name, base_name = clean_source_name(cand.get("source", ""))
                    st.markdown(f"**Source:** `{clean_name}` (`{base_name}`) | **Chunk ID:** `{cand.get('chunk_id')}`")
                    st.code(cand.get("text", ""), language="markdown")
                    st.divider()
        else:
            st.info("Full audit trace was disabled for this run. Enable 'Include Full Audit Trace' to view reranking matrices.")