from dataclasses import dataclass, field
from .hashing import create_chunk_id
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

    chunk_id: str = field(init=False)

    def __post_init__(self):
        self.chunk_id = create_chunk_id(
            self.text,
            self.source,
            self.chunk_index
        )