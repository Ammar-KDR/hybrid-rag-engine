from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingModel:
    name: str
    dimension: int
    