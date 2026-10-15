#!/usr/bin/env python3
"""Official Interactive Demonstration Web UI for 42 Irbid AI Hackathon.

Jordan Civil Status & Passports Department Intelligent RAG Assistant.
Powered by local Cohere Command R7B Arabic & Exact Corpus Grounding.
"""

import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import streamlit as st
from src.hackathon.corpus import HackathonCorpus
from src.hackathon.router import IntentRouter
from src.hackathon.engine import HackathonEngine

# Set Page Config
st.set_page_config(
    page_title="دائرة الأحوال المدنية والجوازات | المساعد الذكي",
    page_icon="🇯🇴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom RTL Arabic Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText, p, h1, h2, h3, h4, span, div {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    /* Header Container */
    .gov-header {
        background: linear-gradient(135deg, #0b2545 0%, #134074 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 4px solid #c59b27;
    }
    
    .gov-title {
        font-size: 26px;
        font-weight: 800;
        margin: 0;
        color: #ffffff;
    }
    
    .gov-subtitle {
        font-size: 15px;
        color: #e0e1dd;
        margin-top: 5px;
        font-weight: 400;
    }

    .status-badge {
        background: rgba(197, 155, 39, 0.2);
        border: 1px solid #c59b27;
        color: #f4d06f;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }

    /* Evidence / Context block */
    .context-card {
        background-color: #f8f9fa;
        border-right: 4px solid #134074;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 13.5px;
        line-height: 1.6;
        color: #2b2d42;
    }
    
    .metric-badge {
        background-color: #e8f4ea;
        color: #1e4620;
        font-size: 12px;
        font-weight: bold;
        padding: 3px 8px;
        border-radius: 12px;
        margin-left: 8px;
    }

    /* St Chat Message Styling */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_engine():
    corpus = HackathonCorpus()
    router = IntentRouter(corpus)
    engine = HackathonEngine(corpus=corpus, router=router, model_name="command-r7b-arabic:7b")
    return corpus, router, engine


corpus, router, engine = load_engine()

# Header HTML
st.markdown("""
<div class="gov-header">
    <div>
        <div class="gov-title">المملكة الأردنية الهاشمية 🇯🇴</div>
        <div class="gov-subtitle">دائرة الأحوال المدنية والجوازات • المساعد الحكومي الاستشاري الذكي</div>
    </div>
    <div style="text-align: left; direction: ltr;">
        <span class="status-badge">⚡ Cohere Command R7B • 100% Offline RAG</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🏛️ معلومات المنظومة")
    st.info(
        "**النموذج:** `command-r7b-arabic:7b`\n\n"
        "**الحالة:** 🟢 متصل ومحلي بالكامل\n\n"
        "**المستندات الرسمية:** 12 دليلاً حكومياً معتمداً\n\n"
        "**الدقة المعيارية:** 100% في الاختبار الشامل"
    )

    st.markdown("---")
    st.markdown("### ⚡ سيناريوهات العرض السريعة (Demo Presets)")
    st.caption("اضغط على أي استفسار لتجربته وعرض التوليد اللحظي والسياقات المرجعية:")

    demo_questions = [
        ("رسوم جواز حسب السن والصلاحية", "عمري 17 سنة وجوازي باقي عليه 3 شهور، قديش رسوم التجديد؟"),
        ("مقارنة رسوم (بدل فاقد vs تالف)", "أيهما أغلى: جواز سفر بدل فاقد للمرة الثانية أم بدل تالف؟"),
        ("فقدان الهوية للمرة الثالثة (الكفالة)", "الهوية الذكية تبعتي ضاعت وهاي ثالث مرة، شو الإجراء والرسوم؟"),
        ("معاملات متعددة في سؤال واحد", "أنا بدي أطلع جواز لأول مرة، وأختي بدها تجدد هويتها، وأبوي بده بدل فاقد لدفتر العائلة. أعطينا التفاصيل لكل واحد بشكل منفصل."),
        ("لهجة عامية أردنية", "الهوية راحت مني، شو لازم أجيب؟"),
        ("سؤال خارج النطاق (رفض نظامي)", "كم رسوم تصديق الشهادة الجامعية من وزارة التعليم العالي؟"),
        ("استفسار غامض (طلب توضيح)", "بدي أجدد، شو الأوراق المطلوبة؟"),
        ("قائمة التحقق الشاملة (9 بنود)", "لو سمحت، اكتبلي قائمة التحقق النهائية لمعاملة جواز سفر بدل فاقد بجميع الحقول الرسمية."),
    ]

    for label, preset_q in demo_questions:
        if st.button(label, use_container_width=True):
            st.session_state["preset_input"] = preset_q

    st.markdown("---")
    if st.button("🔄 محادثة جديدة (مسح الذاكرة)", use_container_width=True, type="secondary"):
        st.session_state["messages"] = []
        st.session_state["history"] = []
        st.rerun()

# Initialize Chat Memory
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "مرحباً بك في المساعد الذكي لدائرة الأحوال المدنية والجوازات الأردنية. كيف يمكنني مساعدتك اليوم في معاملات جواز السفر، البطاقة الذكية، أو دفتر العائلة؟",
            "contexts": [],
            "latency": 0.0,
        }
    ]

if "history" not in st.session_state:
    st.session_state["history"] = []

# Display Conversation History
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display Contexts if present
        if msg.get("contexts"):
            with st.expander(f"📑 السند الرسمي والوثائق المسترجعة ({len(msg['contexts'])} بنود رسمية)"):
                for ctx in msg["contexts"]:
                    if " - " in ctx:
                        header, body = ctx.split(" - ", 1)
                        st.markdown(f"**📌 {header}**")
                        st.markdown(f"> {body.strip()}")
                    else:
                        st.markdown(f"> {ctx}")

# Input prompt handling
preset_q = st.session_state.pop("preset_input", None)
user_query = st.chat_input("اكتب استفسارك هنا باللغة العربية...")

query_to_process = preset_q or user_query

if query_to_process:
    # Append User Message
    st.session_state["messages"].append({
        "role": "user",
        "content": query_to_process,
    })
    with st.chat_message("user"):
        st.markdown(query_to_process)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("جاري استرجاع السند الرسمي وتوليد الإجابة..."):
            t0 = time.perf_counter()
            response = engine.answer_question(
                question=query_to_process,
                history=st.session_state["history"],
            )
            elapsed = time.perf_counter() - t0

            answer_text = response.get("answer", "")
            contexts = response.get("contexts", [])

            # Render Answer
            st.markdown(answer_text)

            # Render Contexts
            if contexts:
                with st.expander(f"📑 السند الرسمي والوثائق المسترجعة ({len(contexts)} بنود رسمية) • ⚡ {elapsed:.2f}s"):
                    for ctx in contexts:
                        if " - " in ctx:
                            header, body = ctx.split(" - ", 1)
                            st.markdown(f"**📌 {header}**")
                            st.markdown(f"> {body.strip()}")
                        else:
                            st.markdown(f"> {ctx}")
            else:
                st.caption(f"⚡ زمن الاستجابة: {elapsed:.2f} ثانية")

    # Update Conversation State
    st.session_state["messages"].append({
        "role": "assistant",
        "content": answer_text,
        "contexts": contexts,
        "latency": elapsed,
    })

    st.session_state["history"].append({
        "question": query_to_process,
        "answer": answer_text,
        "contexts": contexts,
    })
