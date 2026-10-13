# 🏛️ Implementation Plan: 100% Arabic Government AI Assistant
**Target Event**: 42 Irbid Hackathon (PSUT Team)  
**Corpus Domain**: Jordanian & Public Government Services (خدمات حكومية)  
**Operating Environment**: Linux Workstation / Windows Laptop (Offline Air-Gapped via Ollama)  
**Active Branch**: `hackathon-ollama`  

---

## 🎯 Executive Summary & Objectives

The hackathon organizers issued two critical constraints:
1. **Operating System**: Workstations run Linux (laptops permitted if capable of running local models up to 7B via Ollama).
2. **Corpus**: **100% Arabic documents relating to government services.**

Our goal is to transform the existing Hybrid RAG engine into an **Arabic-native, sovereign, institutional intelligence assistant** that sets the gold standard for accuracy, citation rigor, and executive decision-making.

---

## 🏗️ Core Model Architecture (Pre-Cached & Offline-Ready)

| Component | Selected Model | Dimensions / Size | Why Selected |
| :--- | :--- | :--- | :--- |
| **LLM Engine** | **`qwen3.5:4b`** | 3.3 GB / 4B params | Alibaba Qwen 3.5 architecture. Verified fluent formal Arabic (فصحى), lightning-fast generation, under 3.5 GB VRAM footprint leaving 2.5 GB free on RTX 3060. |
| **Dense Embeddings** | **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** | 384 dimensions / ~470 MB | Native Arabic semantic representation. Exact 384-dim drop-in match for our existing Qdrant vector store. |
| **Cross-Encoder Reranker** | **`BAAI/bge-reranker-v2-m3`** | Multilingual XLM-RoBERTa / ~1.1 GB | Cross-lingual reranker natively trained on Arabic. Verified benchmark score: **0.9994** on Arabic query-passage matching. |
| **Sparse / Keyword** | **BM25Okapi + Arabic Normalizer** | In-memory index | Custom Arabic normalizer removing tashkeel, tatweel, normalizing Alef/Yaa/Taa Marbuta, and expanding `ال-` prefixes. |
| **Vector Database** | **Qdrant Embedded** | 384-dim Cosine | Zero external server dependency; runs directly inside application process. |

---

## 📜 Gated Implementation Phases

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Arabic NLP Core Engine (Normalization, Tokenizer, Headings)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 2: Arabic Government Document Chunker (Heading & Context Aware)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 3: Arabic-Enhanced BM25 Retriever (Dual Normalization & Recall)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 4: Model Configuration & Arabic Prompt Engineering               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 5: Streamlit UI Localization (RTL Support, Arabic Cards & Presets)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Phase 6: Linux Workstation Bootstrap Script & End-to-End Verification  │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Arabic NLP Core Engine (`src/rag/nlp/arabic.py`)
- [ ] Create `src/rag/nlp/arabic.py` with pure-Python, zero-dependency functions:
  - `remove_tashkeel(text: str) -> str`: Strips diacritics (`[\u064B-\u065F\u0670]`).
  - `remove_tatweel(text: str) -> str`: Strips kashida (`\u0640`).
  - `normalize_arabic(text: str) -> str`: Unifies Alef (`[إأآٱ]` $\rightarrow$ `ا`), Yaa/Alef Maqsura (`[ى]` $\rightarrow$ `ي`), and Taa Marbuta (`[ة]` $\rightarrow$ `ه`).
  - `tokenize_arabic(text: str) -> list[str]`: Generates normalized tokens with prefix expansion for `ال-` (definite article) and coordinating particles (`و-`, `ب-`, `ل-`).
  - `is_arabic_heading(line: str) -> tuple[bool, str, int]`: Detects official government headings:
    - Clauses: `المادة (X)`, `البند أولاً`, `الفقرة (أ)`
    - Service guides: `شروط الخدمة`, `الوثائق المطلوبة`, `الرسوم المقررة`, `خطوات تقديم الطلب`, `المدة الزمنية`, `قنوات الخدمة`.
  - `split_arabic_sentences(text: str) -> list[str]`: Splits on Arabic punctuation (`.` `،` `؛` `؟` `\n`).
- [ ] Write unit tests in `tests/nlp/test_arabic.py`.

---

### Phase 2: Arabic Government Document Chunker (`src/rag/chunking/arabic_chunker.py`)
- [ ] Implement `ArabicGovernmentChunker`:
  - **Structural Section Extraction**: Segment documents based on detected government headings and legal articles.
  - **Hierarchical Context Injection**: Prepend section breadcrumbs to each chunk (e.g. `[خدمة إصدار جواز السفر > الوثائق المطلوبة]`) to eliminate "orphan" clauses.
  - **Soft Clause Boundary Splitting**: Split oversized sections on Arabic sentence boundaries (`،` `؛` `.` `؟` `\n`) within 1,000–1,400 characters, maintaining 200-character overlap.
  - Preserve chunk metadata: `heading`, `heading_path`, `service_name`, `clause_number`.
- [ ] Integrate into `src/rag/ingestion/pipeline.py`:
  - If text contains Arabic script (`[\u0600-\u06FF]`), route to `ArabicGovernmentChunker`.
- [ ] Write unit tests in `tests/chunking/test_arabic_chunker.py`.

---

### Phase 3: Arabic-Aware BM25 Retrieval
- [ ] Update `src/rag/retrieval/bm25_retrieval.py`:
  - Check if text contains Arabic characters.
  - If Arabic: Apply `tokenize_arabic()` with normalization and prefix expansion.
  - If English: Retain existing regex tokenizer.
- [ ] Verify query-to-document recall:
  - `"شروط تجديد الجواز"` matches `"شُرُوطُ تَجْدِيدِ الجَوَازِ"`.
  - `"خدمة"` matches `"الخدمة"`.
- [ ] Write unit tests in `tests/retrieval/test_bm25_arabic.py`.

---

### Phase 4: Model Configuration & Arabic Prompt Engineering
- [ ] Update `src/rag/config.py`:
  - Default `OLLAMA_MODEL = "qwen3.5:4b"`
  - Default `EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"`
  - Default `RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"`
- [ ] Update `src/rag/generation/prompt.py`:
  - Add bilingual system prompt ensuring formal Arabic (لغة عربية فصحى رسمية) when queried in Arabic.
  - Strict grounding in government clauses with numeric citations `[1]`, `[2]`.
- [ ] Update `src/rag/conversation/rewriter.py`:
  - Add Arabic heuristic triggers (pronouns: `هو`, `هي`, `ذلك`, `تلك`, `عنها`, `منها`, `لها`, `به`).
- [ ] Update `src/rag/comparison/service.py` & `src/rag/briefing/service.py`:
  - Prompt Ollama to generate structured comparisons and executive briefings in formal Arabic.

---

### Phase 5: Streamlit UI Localization & Government Domain Adaptation
- [ ] Update `src/rag/ui/app.py`:
  - Add **RTL (Right-to-Left)** CSS styling with clean Arabic typography (`Cairo`, `Segoe UI`, `Tahoma`).
  - Add **Language Switcher** toggle (🇸🇦 العربية / 🇬🇧 English).
  - Add Jordanian / Government Service Inquiry Presets:
    - *"ما هي الوثائق المطلوبة والرسوم المفروضة لتجديد جواز السفر لأول مرة؟"*
    - *"ما هي الشروط الاستثنائية للحصول على رخصة القيادة الفئة الرابعة؟"*
    - *"مقارنة شاملة بين مسار المعاملة العادية والمعاملة المستعجلة"*
    - *"إيجاز تنفيذي لسياسات ومتطلبات منصة سند الحكومية"*
  - Localize Conflict Detective badges into Arabic:
    - `متطابق (Agreement)`
    - `اختلاف في النطاق أو الإصدار (Scope/Version Difference)`
    - `تعارض محتمل (Possible Conflict)`
    - `أدلة غير كافية (Insufficient Evidence)`
  - Localize Executive Briefing categories:
    - `السياسات والأنظمة (Policies)`
    - `المتطلبات التقنية (Technical)`
    - `الامتثال والشروط (Compliance)`
    - `الإجراءات التنفيذية (Action Items)`

---

### Phase 6: Linux Workstation Bootstrap & Verification
- [ ] Create `scripts/setup_linux.sh`:
  - Installs venv, dependencies, sets `PYTHONPATH="src"`.
- [ ] Create `scripts/run_linux.sh`:
  - Checks Ollama, starts Uvicorn, launches Streamlit.
- [ ] Prepare sample Arabic government service test documents in `data/raw/sample_gov_services/`.
- [ ] Run full test suite: Verify **100% test pass rate**.

---

## 📊 Verification Matrix

| Metric | Target | Verification Method |
| :--- | :--- | :--- |
| **Arabic Normalization Match** | 100% on Tashkeel / Alef variants | Unit test `test_arabic_normalizer` |
| **BM25 Arabic Recall** | > 95% on prefix variants (`ال-`) | Unit test `test_bm25_arabic` |
| **Arabic Chunk Context** | 100% of sub-chunks include heading | Unit test `test_arabic_chunker` |
| **Arabic Generation Quality** | Fluent, grounded formal Arabic | Live API & UI verification with `qwen3.5:4b` |
| **Offline Execution** | 100% offline (zero network calls) | `scripts/preflight_offline.py` |
| **Test Suite Coverage** | 0 regressions, all tests green | `pytest tests/` |
