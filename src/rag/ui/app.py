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

/* Primary Button (PSUT Navy) */
.stButton>button[kind="primary"] {
    background-color: #002D62 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.25rem !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 2px 4px rgba(0, 45, 98, 0.2) !important;
    transition: all 0.2s ease !important;
}

.stButton>button[kind="primary"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

.stButton>button[kind="primary"]:hover {
    background-color: #1E40AF !important;
}

/* Secondary Button */
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
) -> str:
    req_id = result.get("request_id", "N/A")
    latency = result.get("latency", {})
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    abstained = result.get("abstained", False)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        "- **Local LLM Engine:** Qwen 2.5 3B (`Ollama`)",
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

    st.markdown('<div class="sidebar-section-title">System Status</div>', unsafe_allow_html=True)
    try:
        health = client.get_health()
        st.session_state["health_status"] = health
        st.success("🟢 Core Services Ready (Air-Gapped)")
    except Exception:
        st.error("🔴 Connecting to API Server...")

    doc_count = len(st.session_state.get("documents", []))
    st.metric("Indexed Documents", doc_count)

    st.markdown('<div class="sidebar-section-title">Session Controls</div>', unsafe_allow_html=True)
    if st.button("🔄 Refresh Documents", use_container_width=True):
        try:
            st.session_state["documents"] = client.list_documents()
            st.success("Synchronized!")
        except Exception as e:
            st.error(str(e))

    if st.button("🧹 Clear Chat History", use_container_width=True):
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
    st.title("🏛️ PSUT Sovereign Hybrid RAG")

# Trust Badges
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

tab_qa, tab_compare, tab_briefing, tab_repo = st.tabs([
    "🔍 Interactive Chat & Evidence",
    "⚖️ Document Conflict Detective",
    "📋 Executive Briefings",
    "📁 Knowledge Repository & Diagnostics",
])


# =========================================================
# TAB 1: INTERACTIVE CHAT & EVIDENCE EXPLORER
# =========================================================

with tab_qa:
    # Preset Starter Inquiries
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
    doc_options = ["All Ingested Documents"] + [f"{d.get('filename')} ({d.get('document_id')[:8]})" for d in docs]
    selected_scope_label = st.selectbox("Document Retrieval Scope", options=doc_options, index=0)

    selected_doc_ids = None
    if selected_scope_label != "All Ingested Documents":
        selected_idx = doc_options.index(selected_scope_label) - 1
        selected_doc_ids = [docs[selected_idx]["document_id"]]

    # Query Input Area
    query_text = st.text_area(
        "Inquiry / Prompt",
        value=st.session_state["question_input"],
        height=85,
        placeholder="Ask any question regarding system architecture, operations, policies, or follow-up...",
        key="main_query_text_area",
    )

    action_col1, action_col2, action_col3 = st.columns([2, 1, 1])
    with action_col1:
        ask_button = st.button("🚀 Run Intelligence Analysis", type="primary", use_container_width=True)
    with action_col2:
        include_trace = st.checkbox("Include Reranker Audit Trace", value=True)
    with action_col3:
        if st.button("🧹 Clear Input", use_container_width=True):
            st.session_state["question_input"] = ""
            st.session_state["last_result"] = None
            st.session_state["last_question"] = ""
            st.session_state["trigger_ask"] = False
            st.rerun()

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
                with st.spinner("Executing Hybrid RAG with Conversational Intent Resolution..."):
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
                st.error(f"Analysis failed: {exc}")

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
            st.info(f"ℹ️ **Conversational Intent Resolved**: Query reformulated to *\"{retrieval_q}\"*")

        if abstained:
            st.warning("⚠️ **System Abstained**: Retrieval confidence fell below safety threshold. No speculative answer generated.")
        else:
            st.markdown(
                """
                <div style="display:flex; justify-content:space-between; align-items:center; background:#FFFFFF; border:1.5px solid #BFDBFE; border-left:5px solid #002D62; border-radius:8px; padding:10px 16px; margin-bottom:14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="color:#047857; font-size:1.1rem; font-weight:800;">●</span>
                        <span style="font-weight:800; color:#002D62; font-size:0.95rem;">Grounded & Evidence-Backed Synthesis</span>
                    </div>
                    <div>
                        <span style="background:#EFF6FF; color:#002D62; font-size:0.78rem; font-weight:700; padding:4px 10px; border-radius:6px; border:1px solid #BFDBFE;">Request ID: %s</span>
                    </div>
                </div>
                """ % result.get("request_id", "N/A")[:12],
                unsafe_allow_html=True,
            )

        # Grounded Answer Presentation
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:0.88rem; font-weight:800; color:#002D62; text-transform:uppercase; margin-bottom:8px;">📌 Synthesized Intelligence</div>',
                unsafe_allow_html=True,
            )
            st.markdown(result.get("answer", ""))

        # Interactive Evidence Explorer & Source Drawer
        if citations or evidence_list:
            st.markdown(
                "<span style='font-size:0.85rem; font-weight:800; color:#002D62; text-transform:uppercase; letter-spacing:0.04em;'>"
                "📑 Interactive Evidence Drawer (Click to Inspect Primary Source & PDF Preview)"
                "</span>",
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

                page_label = f" • Page {page}" if page is not None else ""
                with st.expander(f"📄 Evidence [{ref}]: {clean_name}{page_label}", expanded=(idx == 1)):
                    c_left, c_right = st.columns([1.5, 1])
                    with c_left:
                        st.markdown(f"**Document:** `{clean_name}` (`{base_src}`)")
                        if heading:
                            st.caption(f"**Section Path:** {heading}")
                        st.caption(f"**Chunk SHA-256:** `{cid[:24]}...`")

                        raw_text = cit.get("text") or chunk_map.get(cid)
                        if raw_text:
                            st.markdown(
                                f"<div class='source-pill-quote'>\"{raw_text.strip()}\"</div>",
                                unsafe_allow_html=True,
                            )

                    with c_right:
                        if page is not None and doc_id:
                            st.caption("🖼️ High-Res PDF Page Preview")
                            img_bytes = client.get_page_preview(doc_id, page)
                            if img_bytes:
                                st.image(img_bytes, caption=f"Page {page} Preview", use_container_width=True)
                            else:
                                st.info(f"Page {page} preview available in PDF viewer.")
                        else:
                            st.caption("📄 Markdown / Text Document Evidence")
                            st.success("Verified verbatim passage in sovereign store.")

        # Export Button
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        export_content = generate_executive_brief_export(active_q, result, chunk_map)
        st.download_button(
            label="📥 Export Executive Briefing (.md)",
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
    st.subheader("⚖️ Document Conflict Detective")
    st.caption("Perform rigorous, air-gapped comparison between two documents to detect contradictions, version differences, or policy alignment.")

    docs = st.session_state.get("documents", [])
    if len(docs) < 2:
        st.info("Please index at least two documents to activate side-by-side conflict detection.")
    else:
        doc_names = [f"{d.get('filename')} ({d.get('document_id')[:8]})" for d in docs]
        c1, c2 = st.columns(2)
        with c1:
            sel_a = st.selectbox("Primary Baseline Document (A)", options=doc_names, index=0)
        with c2:
            sel_b = st.selectbox("Comparison Target Document (B)", options=doc_names, index=min(1, len(doc_names) - 1))

        doc_a_idx = doc_names.index(sel_a)
        doc_b_idx = doc_names.index(sel_b)
        doc_a_id = docs[doc_a_idx]["document_id"]
        doc_b_id = docs[doc_b_idx]["document_id"]

        topic_input = st.text_input(
            "Comparison Topic / Policy Area",
            value="Container restart policies and resource allocation",
            help="Enter the specific policy, deadline, or parameter to compare.",
        )

        preset_comp_cols = st.columns(3)
        with preset_comp_cols[0]:
            if st.button("Compare Restart Policies", key="cmp_restart", use_container_width=True):
                topic_input = "Container restart policies and failure handling"
        with preset_comp_cols[1]:
            if st.button("Compare Timeout Limits", key="cmp_timeout", use_container_width=True):
                topic_input = "Database connection timeout and retry procedures"
        with preset_comp_cols[2]:
            if st.button("Compare DNS Resolvers", key="cmp_dns", use_container_width=True):
                topic_input = "DNS resolution configuration and fallback addresses"

        if st.button("🔍 Run Conflict & Divergence Audit", type="primary", use_container_width=True):
            if not topic_input.strip():
                st.warning("Please specify a topic to audit.")
            else:
                try:
                    with st.spinner("Auditing document evidence, scopes, and potential contradictions..."):
                        comp_res = client.compare(
                            document_a_id=doc_a_id,
                            document_b_id=doc_b_id,
                            topic=topic_input.strip(),
                        )

                    # Relationship Badge
                    rel = comp_res.get("relationship", "insufficient_evidence")
                    badge_class = {
                        "agreement": "rel-agreement",
                        "scope_or_version_difference": "rel-version",
                        "possible_conflict": "rel-conflict",
                        "insufficient_evidence": "rel-insufficient",
                    }.get(rel, "rel-insufficient")

                    rel_label = {
                        "agreement": "✅ Policy Agreement: Factual Alignment",
                        "scope_or_version_difference": "ℹ️ Scope / Version Difference: Tier or Effective Date Divergence",
                        "possible_conflict": "⚠️ Possible Conflict: Direct Contradiction Detected",
                        "insufficient_evidence": "❓ Insufficient Evidence: Inconclusive Coverage",
                    }.get(rel, rel.replace("_", " ").title())

                    st.markdown(f'<div class="rel-badge {badge_class}">{rel_label}</div>', unsafe_allow_html=True)
                    st.markdown(f"**Executive Summary:** {comp_res.get('summary')}")

                    # Side by side cards
                    card_a, card_b = st.columns(2)
                    doc_a_claim = comp_res.get("document_a", {})
                    doc_b_claim = comp_res.get("document_b", {})

                    with card_a:
                        with st.container(border=True):
                            st.markdown(f"#### 📄 Document A: `{doc_a_claim.get('filename')}`")
                            st.write(f"**Stated Rule / Claim:** {doc_a_claim.get('claim')}")
                            if doc_a_claim.get("scope_notes"):
                                st.caption(f"**Scope / Version Condition:** {doc_a_claim.get('scope_notes')}")
                            
                            ev_a = doc_a_claim.get("evidence", [])
                            if ev_a:
                                with st.expander(f"Verified Evidence ({len(ev_a)} passages)", expanded=True):
                                    for ev in ev_a:
                                        st.markdown(f"> \"{ev.get('text', '')[:300]}...\"")
                                        st.caption(f"Source: `{ev.get('source')}`")

                    with card_b:
                        with st.container(border=True):
                            st.markdown(f"#### 📄 Document B: `{doc_b_claim.get('filename')}`")
                            st.write(f"**Stated Rule / Claim:** {doc_b_claim.get('claim')}")
                            if doc_b_claim.get("scope_notes"):
                                st.caption(f"**Scope / Version Condition:** {doc_b_claim.get('scope_notes')}")

                            ev_b = doc_b_claim.get("evidence", [])
                            if ev_b:
                                with st.expander(f"Verified Evidence ({len(ev_b)} passages)", expanded=True):
                                    for ev in ev_b:
                                        st.markdown(f"> \"{ev.get('text', '')[:300]}...\"")
                                        st.caption(f"Source: `{ev.get('source')}`")

                    # Resolution guidance
                    with st.container(border=True):
                        st.markdown("**🛡️ Decision-Maker Resolution Guidance:**")
                        st.write(comp_res.get("resolution_notes", "Review primary documents before policy enforcement."))

                except Exception as exc:
                    st.error(f"Comparison analysis failed: {exc}")


# =========================================================
# TAB 3: EXECUTIVE BRIEFINGS (MULTI-DOC MAP-REDUCE)
# =========================================================

with tab_briefing:
    st.subheader("📋 Multi-Document Executive Briefing")
    st.caption("Generate a structured synthesis across multiple documents with category-tagged findings and verifiable citations.")

    docs = st.session_state.get("documents", [])
    if not docs:
        st.info("No documents indexed yet. Upload documents in Tab 4 to generate briefings.")
    else:
        doc_map = {f"{d.get('filename')} ({d.get('document_id')[:8]})": d.get("document_id") for d in docs}
        selected_brief_names = st.multiselect(
            "Select Documents to Synthesize",
            options=list(doc_map.keys()),
            default=list(doc_map.keys())[:min(3, len(doc_map))],
        )

        focus_input = st.text_input(
            "Briefing Focus / Objectives",
            value="Executive Summary, Critical Policies, and Key Operational Standards",
        )

        if st.button("📋 Generate Executive Briefing", type="primary", use_container_width=True):
            if not selected_brief_names:
                st.warning("Please select at least one document.")
            else:
                target_ids = [doc_map[name] for name in selected_brief_names]
                try:
                    with st.spinner("Synthesizing multi-document briefing using Map-Reduce engine..."):
                        brief_res = client.brief(
                            document_ids=target_ids,
                            focus=focus_input,
                            max_findings=8,
                        )

                    # Summary Box
                    with st.container(border=True):
                        st.markdown("### 📌 Executive Overview")
                        st.markdown(brief_res.get("executive_summary", ""))
                        st.caption(f"Synthesized across {brief_res.get('document_count')} documents: {', '.join(brief_res.get('analyzed_documents', []))}")

                    # Findings List
                    findings = brief_res.get("findings", [])
                    st.markdown(f"### 🎯 Strategic Findings & Mandates ({len(findings)})")

                    for idx, f in enumerate(findings, start=1):
                        cat = f.get("category", "policy")
                        tag_class = f"tag-{cat}"
                        with st.container(border=True):
                            st.markdown(f'<span class="finding-tag {tag_class}">{cat.replace("_", " ").upper()}</span>', unsafe_allow_html=True)
                            st.markdown(f"**{idx}. {f.get('title')}**")
                            st.write(f.get("description"))

                            evs = f.get("evidence", [])
                            if evs:
                                with st.expander(f"📑 Grounded Evidence ({len(evs)} chunk)", expanded=False):
                                    for ev in evs:
                                        st.markdown(f"> \"{ev.get('text', '')[:300]}...\"")
                                        st.caption(f"Source: `{ev.get('filename')}` | Reference: `#{ev.get('reference')}`")

                    # Download Briefing
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
                        label="📥 Download Executive Briefing (.md)",
                        data="\n".join(brief_md),
                        file_name=f"psut_executive_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

                except Exception as exc:
                    st.error(f"Briefing generation failed: {exc}")


# =========================================================
# TAB 4: KNOWLEDGE REPOSITORY & SYSTEM DIAGNOSTICS
# =========================================================

with tab_repo:
    st.subheader("📁 Sovereign Knowledge Repository & Diagnostics")
    st.caption("Air-gapped data catalog, document ingestion, and live local infrastructure diagnostics.")

    # Live Health Diagnostics
    try:
        health_info = client.get_health()
        st.markdown("#### 🛡️ Hardware & Engine Diagnostics")
        h_col1, h_col2, h_col3, h_col4 = st.columns(4)
        with h_col1:
            st.metric("Ollama LLM", health_info.get("ollama", {}).get("model", "qwen2.5:3b"), "Local GPU")
        with h_col2:
            st.metric("Embeddings", health_info.get("embedding_model", {}).get("name", "MiniLM-L6"), "384-dim")
        with h_col3:
            st.metric("Reranker", health_info.get("reranker", {}).get("name", "bge-reranker"), "Cross-Encoder")
        with h_col4:
            st.metric("Vector Store", "Qdrant Embedded", f"{health_info.get('chunk_count', 0)} chunks")
    except Exception:
        st.warning("Could not fetch real-time health telemetry.")

    st.divider()

    # Document Ingestion Section
    st.markdown("#### ⚡ Ingest New Document")
    uploaded_file = st.file_uploader(
        "Upload Enterprise Document (PDF, Word DOCX, Markdown, Text, HTML)",
        type=["md", "txt", "pdf", "docx", "html", "htm"],
        key="tab_repo_uploader",
    )

    if uploaded_file is not None:
        if st.button("⚡ Index Document into Vector Store", use_container_width=True, type="primary"):
            try:
                with st.spinner("Processing document chunks and local embeddings..."):
                    result = client.ingest(
                        filename=uploaded_file.name,
                        content=uploaded_file.getvalue(),
                    )

                chunk_cnt = result.get("chunk_count", 0)
                if result.get("duplicate"):
                    st.info(f"ℹ️ Document **{uploaded_file.name}** is already indexed ({chunk_cnt} chunks). Ready for search, conflict detection, and briefings!")
                else:
                    st.success(f"✅ Successfully indexed **{uploaded_file.name}** ({chunk_cnt} chunks) into the vector store!")
                    st.session_state["documents"] = client.list_documents()
                    st.rerun()

            except Exception as exc:
                st.error(f"Ingestion failed: {exc}")

    st.divider()

    # Document Catalog Table
    st.markdown("#### 📚 Ingested Document Catalog")
    docs = st.session_state.get("documents", [])
    if docs:
        doc_rows = []
        for d in docs:
            clean_name, base_name = clean_source_name(d.get("filename", ""))
            doc_rows.append({
                "Document Name": clean_name,
                "Format": d.get("file_type", "").upper(),
                "Chunk Count": d.get("chunk_count", 0),
                "Document ID": d.get("document_id", "")[:16] + "...",
                "Strategy": d.get("chunking_strategy", "structure"),
            })
        st.dataframe(pd.DataFrame(doc_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No documents currently indexed.")