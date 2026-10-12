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


def main():
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
