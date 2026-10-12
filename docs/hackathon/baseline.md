# Hackathon Baseline Report

**Timestamp:** 2026-10-12  
**Branch:** `hackathon-ollama`  
**Execution Environment:** Windows 11, Python 3.13.5 (hyb_rag venv), NVIDIA GeForce RTX 3060 Laptop GPU  

---

## 1. Test Suite Verification

Pytest run executed against `tests/`:

```text
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
collected 4 items

tests/api/test_documents.py::test_list_documents PASSED                  [ 25%]
tests/api/test_ingest.py::test_ingest_success PASSED                     [ 50%]
tests/api/test_ingest.py::test_ingest_duplicate PASSED                   [ 75%]
tests/api/test_ingest.py::test_unsupported_file_returns_400 PASSED       [100%]

============================= 4 passed in 39.48s ==============================
```

**Status:** 100% Green (4/4 passed).

---

## 2. Active Component Architecture

| Component | Technology | Configuration / Status |
| :--- | :--- | :--- |
| **LLM Inference** | Ollama (`qwen2.5:3b`) | 100% GPU offload (37/37 layers, 2.16 GB VRAM, `keep_alive: -1`) |
| **Dense Retrieval** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Local PyTorch, 384-dim embeddings |
| **Sparse Retrieval** | `rank_bm25.BM25Okapi` | Chunk tokenization & JSONL index |
| **Fusion & Rerank** | Reciprocal Rank Fusion (RRF) + BGE Cross-Encoder | `BAAI/bge-reranker-base` local inference |
| **Vector Database** | Embedded Qdrant | `data/qdrant_storage` |
| **API Server** | FastAPI / Uvicorn | `http://127.0.0.1:8000` |
| **Front-End UI** | Streamlit | `http://localhost:8501` (PSUT White & Blue theme) |

---

## 3. Baseline API Contracts

### `POST /v1/ask`
- **Request Body:**
  ```json
  {
    "query": "string",
    "top_k": 5
  }
  ```
- **Response Body:**
  ```json
  {
    "query": "string",
    "answer": "string",
    "sources": [
      {
        "document_id": "string",
        "chunk_id": "string",
        "text": "string",
        "score": 0.85
      }
    ],
    "latency_ms": 120.5
  }
  ```

### `POST /v1/ingest`
- **Request:** `multipart/form-data` with `file: UploadFile`
- **Response Body:**
  ```json
  {
    "document_id": "string",
    "filename": "string",
    "chunk_count": 12,
    "message": "Document ingested successfully"
  }
  ```

### `GET /v1/documents`
- **Response Body:**
  ```json
  [
    {
      "document_id": "string",
      "filename": "string",
      "chunk_count": 12,
      "created_at": "2026-10-12T14:30:00Z"
    }
  ]
  ```

---

## 4. Safety & Sanitation Audit

- **Input Ingestion Logging:** Removed raw byte stdout dumping (`print(content)`) in `src/rag/api/routes/ingest.py`.
- **Prompt Safety:** Citations enforce bracket markers with zero-drop fallback to top reranked evidence chunk.
- **Data Privacy:** 100% local processing; zero data transmission to external APIs.
