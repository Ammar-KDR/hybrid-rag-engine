from pathlib import Path
import os


class Settings:

    QDRANT_URL = os.getenv(
        "QDRANT_URL",
        "http://localhost:6333",
    )

    QDRANT_COLLECTION = os.getenv(
        "QDRANT_COLLECTION",
        "documents",
    )

    LM_STUDIO_BASE_URL = os.getenv(
        "LM_STUDIO_BASE_URL",
        "http://localhost:1234/v1",
    )

    LM_STUDIO_MODEL = os.getenv(
        "LM_STUDIO_MODEL",
        "qwen/qwen3-4b-2507",
    )

    # ============================================================
    # LLM Settings (Ollama / LM Studio / Gemini)
    # ============================================================

    LLM_BACKEND = os.getenv(
        "LLM_BACKEND",
        "ollama",
    ).lower()

    OLLAMA_BASE_URL = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434/v1",
    )

    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL",
        "qwen3.5:4b",
    )

    ENABLE_VERIFICATION = os.getenv(
        "ENABLE_VERIFICATION",
        "false",
    ).lower() in ("true", "1", "yes")

    # ============================================================
    # Vector Database Settings
    # ============================================================

    QDRANT_STORAGE_MODE = os.getenv(
        "QDRANT_STORAGE_MODE",
        "local",
    ).lower()

    # ============================================================
    # Models
    # ============================================================

    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    RERANKER_MODEL_NAME = os.getenv(
        "RERANKER_MODEL_NAME",
        "BAAI/bge-reranker-v2-m3",
    )

    # ============================================================
    # Hackathon Corpus Root & Isolation Profile
    # ============================================================
    _corpus_root = os.getenv("HACKATHON_CORPUS_ROOT")

    DATA_PATH = (
        Path(_corpus_root) / "raw"
        if _corpus_root
        else Path(os.getenv("DATA_PATH", "data/raw"))
    )

    CHUNK_STORE_PATH = (
        Path(_corpus_root) / "indexes/chunks.jsonl"
        if _corpus_root
        else Path(os.getenv("CHUNK_STORE_PATH", "data/indexes/chunks.jsonl"))
    )

    REGISTRY_PATH = (
        Path(_corpus_root) / "registry.json"
        if _corpus_root
        else Path(os.getenv("REGISTRY_PATH", "data/registry.json"))
    )

    SERVICES_MANIFEST_PATH = (
        Path(_corpus_root) / "services_manifest.json"
        if _corpus_root
        else Path(os.getenv("SERVICES_MANIFEST_PATH", "data/services_manifest.json"))
    )

    QDRANT_LOCAL_PATH = (
        Path(_corpus_root) / "qdrant_storage"
        if _corpus_root
        else Path(os.getenv("QDRANT_LOCAL_PATH", "data/qdrant_storage"))
    )

    # ============================================================
    # Competition Accuracy & Grounding Modes
    # ============================================================
    GOV_SERVICE_MODE = os.getenv(
        "GOV_SERVICE_MODE", "true"
    ).lower() in ("true", "1", "yes")

    STRICT_CITATIONS = os.getenv(
        "STRICT_CITATIONS", "true"
    ).lower() in ("true", "1", "yes")

    ENABLE_CHARTS = os.getenv(
        "ENABLE_CHARTS", "false"
    ).lower() in ("true", "1", "yes")

    OCR_ENABLED = os.getenv(
        "OCR_ENABLED", "false"
    ).lower() in ("true", "1", "yes")

    RERANKER_ENABLED = os.getenv(
        "RERANKER_ENABLED", "true"
    ).lower() in ("true", "1", "yes")

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )


settings = Settings()