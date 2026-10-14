"""Service-aware context builder for Jordan Government Services RAG.

Budgets and packages complete short service records or closely coupled sections
(eligibility + fees + exceptions) into evidence blocks, preventing loss of
conditional clauses while strictly adhering to the Ollama token budget.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Dict, List, Optional
from rag.generation.model import BuiltContext, ContextBlock
from rag.ingestion.service_manifest import ServiceRecord
from rag.reranking.model import RerankedChunk
from rag.nlp.arabic import normalize_arabic


class ServiceContextBuilder:
    """Constructs service-scoped, exception-preserving context for local LLMs."""

    def __init__(
        self,
        max_context_tokens: int = 3500,
        chars_per_token: float = 3.5,
    ):
        self.max_context_tokens = max_context_tokens
        self.chars_per_token = chars_per_token
        self.max_context_chars = int(max_context_tokens * chars_per_token)

    def build_from_service(
        self,
        service: ServiceRecord,
        query: str,
        retrieved_chunks: Optional[List[RerankedChunk]] = None,
    ) -> BuiltContext:
        """Assembles context for a single routed service."""
        blocks: List[ContextBlock] = []
        accumulated_chars = 0
        ref_counter = 1

        # 1. If full service fits in budget, include all raw sections in order
        total_service_chars = sum(len(s.get("original_text", "")) for s in service.raw_sections)

        if total_service_chars <= self.max_context_chars and service.raw_sections:
            for sec in service.raw_sections:
                span = sec.get("source_span", {})
                heading = sec.get("heading")
                sec_type = sec.get("section_type", "other")
                text = sec.get("original_text", "").strip()
                if not text:
                    continue

                heading_path = [service.service_name]
                if heading:
                    heading_path.append(heading)

                block = ContextBlock(
                    reference=ref_counter,
                    chunk_id=sec.get("section_id", f"{service.service_id}_{ref_counter}"),
                    text=unicodedata.normalize("NFKC", text),
                    source=span.get("filename", service.service_name),
                    page_number=span.get("page_number"),
                    heading_path=heading_path,
                )
                blocks.append(block)
                ref_counter += 1

            return self._finalize_context(blocks)

        # 2. If service exceeds budget, prioritize retrieved chunks belonging to this service
        # and ensure exception/fee sections are not omitted
        if retrieved_chunks:
            # Sort chunks prioritizing fee/exception sections
            prioritized = []
            for chk in retrieved_chunks:
                sec_type = chk.metadata.get("section_type", "")
                is_critical = sec_type in ("fees", "exceptions", "eligibility", "requirements")
                prioritized.append((0 if is_critical else 1, chk))

            prioritized.sort(key=lambda x: x[0])

            for _, chk in prioritized:
                text = unicodedata.normalize("NFKC", chk.text.strip())
                if accumulated_chars + len(text) > self.max_context_chars and blocks:
                    break

                meta = chk.metadata or {}
                block = ContextBlock(
                    reference=ref_counter,
                    chunk_id=chk.chunk_id,
                    text=text,
                    source=meta.get("filename") or meta.get("source", ""),
                    page_number=meta.get("page_number"),
                    heading_path=meta.get("heading_path", [service.service_name]),
                )
                blocks.append(block)
                accumulated_chars += len(text)
                ref_counter += 1

        return self._finalize_context(blocks)

    def build_comparison(
        self,
        services: List[ServiceRecord],
        query: str,
    ) -> BuiltContext:
        """Assembles context for a two-service comparison query with labeled blocks."""
        blocks: List[ContextBlock] = []
        ref_counter = 1
        per_service_budget = self.max_context_chars // max(len(services), 1)

        for svc in services:
            svc_chars = 0
            for sec in svc.raw_sections:
                text = sec.get("original_text", "").strip()
                if not text:
                    continue
                if svc_chars + len(text) > per_service_budget and svc_chars > 0:
                    break

                span = sec.get("source_span", {})
                heading = sec.get("heading")
                heading_path = [svc.service_name]
                if heading:
                    heading_path.append(heading)

                block = ContextBlock(
                    reference=ref_counter,
                    chunk_id=sec.get("section_id", f"{svc.service_id}_{ref_counter}"),
                    text=unicodedata.normalize("NFKC", text),
                    source=span.get("filename", svc.service_name),
                    page_number=span.get("page_number"),
                    heading_path=heading_path,
                )
                blocks.append(block)
                svc_chars += len(text)
                ref_counter += 1

        return self._finalize_context(blocks)

    def _finalize_context(self, blocks: List[ContextBlock]) -> BuiltContext:
        text_lines = []
        for b in blocks:
            header_parts = [f"المرجع [{b.reference}]"]
            if b.heading_path:
                header_parts.append(" > ".join(b.heading_path))
            if b.source:
                header_parts.append(f"الملف: {b.source}")
            if b.page_number is not None:
                header_parts.append(f"الصفحة: {b.page_number}")

            header_str = " | ".join(header_parts)
            text_lines.append(f"[{header_str}]\n{b.text}")

        full_text = "\n\n".join(text_lines)
        return BuiltContext(text=full_text, blocks=blocks)
