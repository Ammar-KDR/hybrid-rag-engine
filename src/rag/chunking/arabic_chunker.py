from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from rag.ingestion.model import Document, Chunk
from rag.nlp.arabic import (
    is_arabic_heading,
    split_arabic_sentences,
    normalize_arabic,
)


class ArabicGovernmentChunker:
    """
    Structure-aware, hierarchical chunker optimized for Arabic government service guides,
    legal clauses, and official circulars.
    
    Key features:
    1. Automatic detection of Arabic government headings (شروط, وثائق, رسوم, إجراءات, مواد).
    2. Hierarchical Context Injection: prepends breadcrumb context to chunks to prevent orphan clauses.
    3. Soft clause-boundary splitting on Arabic punctuation (، ؛ . ؟).
    """

    def __init__(
        self,
        max_chunk_chars: int = 1200,
        overlap: int = 200,
        inject_heading_context: bool = True,
    ):
        if max_chunk_chars <= 0:
            raise ValueError("max_chunk_chars must be a positive integer.")
        if overlap < 0 or overlap >= max_chunk_chars:
            raise ValueError("overlap must be non-negative and less than max_chunk_chars.")

        self.max_chunk_chars = max_chunk_chars
        self.overlap = overlap
        self.inject_heading_context = inject_heading_context

    def extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts structural sections based on detected Arabic government headings.
        """
        lines = text.split("\n")
        sections: List[Dict[str, Any]] = []

        current_heading: Optional[str] = None
        current_level = 1
        current_lines: List[str] = []
        heading_path: List[str] = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            is_head, title, level = is_arabic_heading(trimmed)
            if is_head:
                # Save previous section if it has content
                if current_lines:
                    body = "\n".join(current_lines).strip()
                    if body:
                        sections.append({
                            "heading": current_heading,
                            "level": current_level,
                            "heading_path": list(heading_path),
                            "text": body,
                        })
                    current_lines = []

                current_heading = title
                current_level = level
                # Update heading breadcrumb hierarchy
                if level == 1:
                    heading_path = [title]
                elif level == 2:
                    heading_path = heading_path[:1] + [title] if heading_path else [title]
                else:
                    heading_path.append(title)
            else:
                current_lines.append(trimmed)

        # Flush final section
        if current_lines:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append({
                    "heading": current_heading,
                    "level": current_level,
                    "heading_path": list(heading_path),
                    "text": body,
                })

        return sections

    def chunk(self, document: Document) -> List[Chunk]:
        """
        Chunks an Arabic document into hierarchical, context-enriched Chunk objects.
        """
        if not document.text or not document.text.strip():
            return []

        sections = self.extract_sections(document.text)
        if not sections:
            # Fallback if no headings detected: treat as single raw section
            sections = [{
                "heading": None,
                "level": 1,
                "heading_path": [],
                "text": document.text.strip(),
            }]

        chunks: List[Chunk] = []
        chunk_idx = 0

        # Attempt to infer document service title from source filename or first heading
        doc_filename = Path(document.source).name if document.source else ""
        service_name = (
            sections[0]["heading"]
            if (sections and sections[0]["heading"])
            else doc_filename
        )

        for section in sections:
            heading = section.get("heading")
            heading_path = section.get("heading_path", [])
            body_text = section.get("text", "")

            # Build contextual breadcrumb prefix
            breadcrumb_parts = [p for p in heading_path if p]
            if not breadcrumb_parts and heading:
                breadcrumb_parts = [heading]
            breadcrumb = " > ".join(breadcrumb_parts)

            # If section fits within budget, keep as a single chunk
            if len(body_text) <= self.max_chunk_chars:
                final_text = (
                    f"[{breadcrumb}]\n{body_text}"
                    if (self.inject_heading_context and breadcrumb)
                    else body_text
                )
                metadata = {
                    **document.metadata,
                    "heading": heading,
                    "heading_path": heading_path,
                    "breadcrumb": breadcrumb,
                    "service_name": service_name,
                    "section_part": 1,
                    "total_parts": 1,
                }
                chunks.append(
                    Chunk(
                        text=final_text,
                        source=document.source,
                        file_type=document.file_type,
                        chunk_index=chunk_idx,
                        chunking_strategy="arabic_government_structure",
                        metadata=metadata,
                    )
                )
                chunk_idx += 1
            else:
                # Split large section on Arabic sentence / clause boundaries
                sentences = split_arabic_sentences(body_text)
                sub_chunks = self._pack_sentences(sentences)

                for part_idx, sub_text in enumerate(sub_chunks, start=1):
                    prefix = f"[{breadcrumb} - جزء {part_idx}]" if breadcrumb else f"[جزء {part_idx}]"
                    final_text = (
                        f"{prefix}\n{sub_text}"
                        if self.inject_heading_context
                        else sub_text
                    )
                    metadata = {
                        **document.metadata,
                        "heading": heading,
                        "heading_path": heading_path,
                        "breadcrumb": breadcrumb,
                        "service_name": service_name,
                        "section_part": part_idx,
                        "total_parts": len(sub_chunks),
                    }
                    chunks.append(
                        Chunk(
                            text=final_text,
                            source=document.source,
                            file_type=document.file_type,
                            chunk_index=chunk_idx,
                            chunking_strategy="arabic_government_structure",
                            metadata=metadata,
                        )
                    )
                    chunk_idx += 1

        return chunks

    def _pack_sentences(self, sentences: List[str]) -> List[str]:
        """
        Packs sentences into chunks up to max_chunk_chars while maintaining overlap.
        """
        if not sentences:
            return []

        chunks: List[str] = []
        current_sentences: List[str] = []
        current_len = 0

        for sentence in sentences:
            sent_len = len(sentence)
            if current_len + sent_len + 1 > self.max_chunk_chars and current_sentences:
                # Flush current chunk
                chunk_str = " ".join(current_sentences)
                chunks.append(chunk_str)

                # Keep trailing sentences for overlap
                overlap_len = 0
                overlap_sentences: List[str] = []
                for s in reversed(current_sentences):
                    if overlap_len + len(s) <= self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break

                current_sentences = overlap_sentences + [sentence]
                current_len = sum(len(s) for s in current_sentences) + len(current_sentences) - 1
            else:
                current_sentences.append(sentence)
                current_len += sent_len + 1

        if current_sentences:
            chunks.append(" ".join(current_sentences))

        return chunks
