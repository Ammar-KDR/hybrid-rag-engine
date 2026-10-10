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
        "qwen2.5:3b",
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

    QDRANT_LOCAL_PATH = Path(
        os.getenv(
            "QDRANT_LOCAL_PATH",
            "data/qdrant_storage",
        )
    )

    # ============================================================
    # Models
    # ============================================================

    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    RERANKER_MODEL_NAME = os.getenv(
        "RERANKER_MODEL_NAME",
        "BAAI/bge-reranker-base",
    )

    DATA_PATH = Path(
        os.getenv(
            "DATA_PATH",
            "data/raw",
        )
    )

    CHUNK_STORE_PATH = Path(
        os.getenv(
            "CHUNK_STORE_PATH",
            "data/indexes/chunks.jsonl",
        )
    )

    REGISTRY_PATH = Path(
        os.getenv(
            "REGISTRY_PATH",
            "data/registry.json",
        )
    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )


settings = Settings()