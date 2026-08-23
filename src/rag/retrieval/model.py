from dataclasses import dataclass
from typing import Any
@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict[str,any]
    score: float
    rank: int