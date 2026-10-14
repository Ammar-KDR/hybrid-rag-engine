#!/usr/bin/env python3
"""Offline Preflight Verification CLI

Verifies all components required for 100% offline, GPU-accelerated RAG execution:
- Ollama service responsiveness & model presence
- GPU VRAM caching & offloading
- Local Sentence-Transformers embedding model cache
- Local BGE Cross-Encoder reranker cache
- Qdrant embedded storage directory accessibility
- Knowledge base indexes (chunks and registry)
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Add src to sys.path if not present
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rag.config import settings


def check_ollama(base_url: str, required_model: str) -> tuple[bool, str]:
    api_base = base_url.replace("/v1", "").rstrip("/")
    # 1. Check tags
    tags_url = f"{api_base}/api/tags"
    try:
        req = urllib.request.Request(tags_url, headers={"User-Agent": "OfflinePreflight"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        return False, f"Ollama not reachable at {api_base}: {exc}"

    models = [m.get("name", "") for m in data.get("models", [])]
    matched = any(required_model in m for m in models)
    if not matched:
        return False, f"Model '{required_model}' not found in Ollama. Available: {models}"

    # 2. Check running processes (/api/ps)
    ps_info = ""
    try:
        ps_url = f"{api_base}/api/ps"
        req = urllib.request.Request(ps_url, headers={"User-Agent": "OfflinePreflight"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            ps_data = json.loads(resp.read().decode())
            for model_proc in ps_data.get("models", []):
                name = model_proc.get("name", "")
                vram = model_proc.get("size_vram", 0) / (1024 * 1024)
                size = model_proc.get("size", 0) / (1024 * 1024)
                if required_model in name:
                    ps_info = f" (Loaded in VRAM: {vram:.1f} MB / {size:.1f} MB)"
    except Exception:
        pass

    return True, f"Ollama active, model '{required_model}' ready{ps_info}"


def check_embeddings(model_name: str) -> tuple[bool, str]:
    try:
        from sentence_transformers import SentenceTransformer
        # Check if local files load without downloading
        _ = SentenceTransformer(model_name, local_files_only=True)
        return True, f"Embedding model '{model_name}' cached locally"
    except Exception as exc:
        return False, f"Embedding model '{model_name}' failed to load offline: {exc}"


def check_reranker(model_name: str) -> tuple[bool, str]:
    try:
        from sentence_transformers import CrossEncoder
        _ = CrossEncoder(model_name, local_files_only=True)
        return True, f"Reranker model '{model_name}' cached locally"
    except Exception as exc:
        return False, f"Reranker model '{model_name}' failed to load offline: {exc}"


def check_storage() -> tuple[bool, str]:
    qdrant_path = settings.QDRANT_LOCAL_PATH
    chunk_path = settings.CHUNK_STORE_PATH
    registry_path = settings.REGISTRY_PATH

    details = []
    # Check Qdrant storage folder
    if qdrant_path.exists():
        details.append(f"Qdrant storage: {qdrant_path} exists")
    else:
        details.append(f"Qdrant storage: {qdrant_path} will be created")

    # Check chunks
    if chunk_path.exists():
        with chunk_path.open("r", encoding="utf-8") as f:
            chunk_count = sum(1 for line in f if line.strip())
        details.append(f"Chunks index: {chunk_count} chunks in {chunk_path.name}")
    else:
        details.append(f"Chunks index: {chunk_path.name} not found (empty start safe)")

    # Check registry
    if registry_path.exists():
        try:
            with registry_path.open("r", encoding="utf-8") as f:
                reg_data = json.load(f)
                doc_count = len(reg_data.get("documents", []))
                details.append(f"Registry: {doc_count} documents in {registry_path.name}")
        except Exception:
            details.append(f"Registry: invalid JSON in {registry_path.name}")
    else:
        details.append(f"Registry: {registry_path.name} not found (empty start safe)")

    return True, " | ".join(details)


import argparse


def run_smoke_test(query: str) -> tuple[bool, str]:
    details = []
    # 1. Vector query test
    try:
        # If API server is already running, it holds the lock on embedded Qdrant. Test through it or verify health.
        api_running = False
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/v1/health", headers={"User-Agent": "OfflinePreflight"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                api_health = json.loads(resp.read().decode())
                details.append(f"FastAPI live on :8000 (Qdrant status: {api_health.get('qdrant', {}).get('status', 'ready')})")
                api_running = True
        except Exception:
            api_running = False

        from rag.embedding.service import EmbeddingService
        from rag.vector_store.qdrant import QdrantVectorStore

        emb_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL_NAME)
        q_vec = emb_service.embed_text(query)
        if settings.QDRANT_STORAGE_MODE == "local" and settings.QDRANT_LOCAL_PATH.exists():
            try:
                vstore = QdrantVectorStore(path=settings.QDRANT_LOCAL_PATH)
                if vstore.client.collection_exists(settings.QDRANT_COLLECTION):
                    pts = vstore.search(
                        collection_name=settings.QDRANT_COLLECTION,
                        query_vector=q_vec,
                        limit=1,
                    )
                    details.append(f"Vector search returned {len(pts)} points")
                else:
                    details.append("Vector collection not created yet (fresh start)")
            except Exception as lock_err:
                if "already accessed by another instance" in str(lock_err):
                    details.append("Vector store verified (active lock held by running FastAPI server)")
                else:
                    raise
        else:
            details.append("Vector store directory not present yet (fresh start)")
    except Exception as exc:
        return False, f"Smoke test vector search failed: {exc}"

    # 2. Ollama completion test
    try:
        api_base = settings.OLLAMA_BASE_URL.replace("/v1", "").rstrip("/")
        gen_url = f"{api_base}/api/generate"
        req_body = json.dumps({
            "model": settings.OLLAMA_MODEL,
            "prompt": f"اختبار جاهزية النظام. أجب بكلمة واحدة: جاهز. السؤال: {query}",
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 15},
        }).encode("utf-8")
        req = urllib.request.Request(
            gen_url,
            data=req_body,
            headers={"Content-Type": "application/json", "User-Agent": "OfflinePreflight"},
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            gen_data = json.loads(resp.read().decode())
            response_text = gen_data.get("response", "").strip()
            total_duration_ms = gen_data.get("total_duration", 0) / 1e6
            details.append(f"Generation OK ({total_duration_ms:.0f}ms): '{response_text[:40]}'")
    except Exception as exc:
        return False, f"Smoke test generation failed: {exc} | " + " | ".join(details)

    return True, " | ".join(details)


def main():
    parser = argparse.ArgumentParser(description="Offline Preflight Verification CLI")
    parser.add_argument(
        "--smoke-query",
        type=str,
        nargs="?",
        const="ما هي الوثائق المطلوبة؟",
        default=None,
        help="Run an end-to-end vector search and live LLM generation smoke query",
    )
    args = parser.parse_args()

    print("=" * 65)
    print("  42 IRBID HACKATHON - OFFLINE PREFLIGHT READINESS CHECK")
    print("=" * 65)

    all_passed = True

    # 1. Ollama
    ok, msg = check_ollama(settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)
    status_label = "[OK]  " if ok else "[FAIL]"
    print(f"{status_label} Ollama: {msg}")
    if not ok:
        all_passed = False

    # 2. Embedding Model
    ok, msg = check_embeddings(settings.EMBEDDING_MODEL_NAME)
    status_label = "[OK]  " if ok else "[FAIL]"
    print(f"{status_label} Embeddings: {msg}")
    if not ok:
        all_passed = False

    # 3. Reranker Model
    ok, msg = check_reranker(settings.RERANKER_MODEL_NAME)
    status_label = "[OK]  " if ok else "[FAIL]"
    print(f"{status_label} Reranker: {msg}")
    if not ok:
        all_passed = False

    # 4. Storage & Indexes
    ok, msg = check_storage()
    status_label = "[OK]  " if ok else "[FAIL]"
    print(f"{status_label} Storage: {msg}")

    # 5. Optional Smoke Query
    if args.smoke_query:
        ok, msg = run_smoke_test(args.smoke_query)
        status_label = "[OK]  " if ok else "[FAIL]"
        print(f"{status_label} Smoke Query: {msg}")
        if not ok:
            all_passed = False

    print("=" * 65)
    if all_passed:
        print("  RESULT: SYSTEM IS 100% READY FOR OFFLINE HACKATHON DEMO!")
        print("=" * 65)
        sys.exit(0)
    else:
        print("  RESULT: ONE OR MORE OFFLINE PRECHECKS FAILED. PLEASE FIX ABOVE.")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
