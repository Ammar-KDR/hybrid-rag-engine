from dataclasses import dataclass
from typing import Optional

@dataclass
class ContextBlock:
    reference: int
    chunk_id: str
    text: str
    source: Optional[str] = None
    file_type: Optional[str] = None
    page_number: Optional[int] = None
    heading_path: Optional[list[str]] = None


@dataclass
class BuiltContext:
    text: str
    blocks: list[ContextBlock]

    def get_block(self, reference: int) -> Optional[ContextBlock]:
        for block in self.blocks:
            if block.reference == reference:
                return block

        return None

@dataclass
class GenerationPrompt:
    system_prompt: str
    user_prompt: str

@dataclass
class GenerationResult:
    text: str
    model: str

    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None

    latency_ms: float

@dataclass
class Citation:
    reference: int
    chunk_id: str

    source: str | None = None
    page_number: int | None = None
    heading_path: list[str] | None = None

@dataclass
class GeneratedAnswer:
    question: str
    answer: str

    citations: list[Citation]
    unresolved_references: list[int]
    evidence: list[ContextBlock]

    model: str

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    latency_ms: float | None = None
