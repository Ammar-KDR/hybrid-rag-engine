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