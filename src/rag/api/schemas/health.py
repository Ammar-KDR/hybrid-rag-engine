from pydantic import BaseModel
from typing import Optional


class ComponentStatus(BaseModel):
    ready: bool
    name: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    offline_mode: bool
    ollama: ComponentStatus
    qdrant: ComponentStatus
    embedding_model: ComponentStatus
    reranker: ComponentStatus
    document_count: int
    chunk_count: int
