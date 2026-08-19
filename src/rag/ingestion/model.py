from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    text: str
    source: str
    file_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    text: str
    source: str
    file_type: str
    chunk_index: int
    chunking_strategy: str
    metadata: dict[str, Any] = field(default_factory=dict)