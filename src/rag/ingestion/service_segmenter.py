"""Deterministic service boundary detector and segmenter for Jordan Government RAG.

Handles both separate files (one service per file) and combined documents
(multiple services in one file, across pages or on shared pages), generating
stable service_id, structured sections, and verified metadata.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rag.chunking.arabic_chunker import ArabicGovernmentChunker
from rag.ingestion.model import Chunk, Document
from rag.ingestion.service_manifest import (
    ServiceRecord,
    ServiceSection,
    SourceSpan,
    classify_section_type,
    generate_service_aliases,
)
from rag.nlp.arabic import is_arabic_heading, normalize_arabic


SERVICE_ANCHOR_PATTERNS = [
    re.compile(r"^(?:اسم\s+الخدمة|اسم\s+الخدمه|عنوان\s+الخدمة|عنوان\s+الخدمه)[:\s]+(.+)$", re.IGNORECASE),
    re.compile(r"^(?:بطاقة\s+الخدمة|بطاقه\s+الخدمه|دليل\s+الخدمة|دليل\s+الخدمه)[:\s]+(.+)$", re.IGNORECASE),
    re.compile(r"^(?:خدمة|خدمه)\s+(إصدار|اصدار|تجديد|الحصول\s+على|طلب|استخراج|إلغاء|الغاء|نقل|تسجيل|شطب)\s+(.+)$", re.IGNORECASE),
    re.compile(
        r"^(?:\d{4}\s+)?(?:دليل|تعليمات|إجراءات|اجراءات|بطاقة|بطاقه|خدمة|خدمه|نظام)"
        r"(?:\s+(?:إجراءات|اجراءات|تعليمات|شروط|نظام))?\s+"
        r"(?:إصدار|اصدار|تجديد|ترخيص|نقل|الاشتراك|اشتراك|طلب|الحصول|شهادة|شهاده|استخراج|إلغاء|الغاء|تسجيل|شطب|معاملات|معاملة|معامله|بدل)\s+(.+)$",
        re.IGNORECASE,
    ),
    re.compile(r".*الخدم[ةه]\s+رقم\s*(\d+).*", re.IGNORECASE),
]

SECTION_KEYWORDS = {
    "الرسوم", "رسوم", "الشروط", "شروط", "الوثائق", "وثائق", "المستندات",
    "الأوراق", "الاوراق", "الإجراءات", "اجراءات", "الخطوات", "خطوات",
    "المدة", "المده", "الوقت", "القنوات", "قنوات", "المستفيدون", "استثناءات",
}


def is_service_boundary_line(line: str) -> Tuple[bool, Optional[str]]:
    """Checks if a text line constitutes an explicit service start anchor."""
    clean = line.strip()
    if not clean:
        return False, None

    # Check explicit patterns
    for pat in SERVICE_ANCHOR_PATTERNS:
        m = pat.match(clean)
        if m:
            clean_no_year = re.sub(r"^\d{4}\s+", "", clean)
            clean_no_prefix = re.sub(
                r"^(?:اسم|عنوان|بطاقة|بطاقه|دليل)\s+الخدم[ةه][:\s]+", "", clean_no_year
            ).strip()
            title = re.sub(r"[:：\-ـ\s]+$", "", clean_no_prefix).strip()
            return True, title

    # Check Markdown H1 (# ...) that is not a generic section keyword
    if clean.startswith("# "):
        title = clean[2:].strip()
        norm_title = normalize_arabic(title)
        if not any(kw in norm_title for kw in SECTION_KEYWORDS) and len(title) > 3:
            return True, title

    return False, None


class ServiceSegmenter:
    """Segments extracted documents into typed, stable ServiceRecords."""

    def __init__(self, overrides_path: Optional[Path] = None):
        self.overrides_path = overrides_path
        self._overrides_data = self._load_overrides()

    def _load_overrides(self) -> Dict[str, Any]:
        if not self.overrides_path or not self.overrides_path.exists():
            return {}
        try:
            with open(self.overrides_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def segment(
        self,
        documents: List[Document],
        document_id: str,
        filename: str,
    ) -> List[ServiceRecord]:
        """Segments one or more page documents from a single source file into ServiceRecords."""
        if not documents:
            return []

        # Check manual overrides first
        override_services = self._get_override_services(document_id, filename)
        if override_services:
            return self._apply_overrides(documents, document_id, filename, override_services)

        # Automatic boundary detection
        anchor_points = self._detect_anchors(documents)

        # Single service document (common case: 1 service per file or no multi-anchors)
        if len(anchor_points) <= 1:
            service_name = (
                anchor_points[0]["title"]
                if anchor_points
                else self._infer_service_title(documents, filename)
            )
            return [
                self._build_single_service(
                    documents=documents,
                    document_id=document_id,
                    filename=filename,
                    service_name=service_name,
                    service_idx=1,
                    review_status="reviewed" if anchor_points else "needs_review",
                )
            ]

        # Multi-service combined document (e.g. 1 PDF containing multiple services)
        return self._build_multi_services(documents, document_id, filename, anchor_points)

    def _detect_anchors(self, documents: List[Document]) -> List[Dict[str, Any]]:
        anchors = []
        for doc in documents:
            page_num = doc.metadata.get("page_number", 1)
            lines = doc.text.split("\n")
            for line_idx, line in enumerate(lines):
                clean = line.strip()
                is_anchor, title = is_service_boundary_line(clean)
                if is_anchor and title:
                    # If anchor title was a generic marker like "الخدمة رقم" or number, inspect next line
                    if ("الخدمة رقم" in title or "الخدمه رقم" in title) and line_idx + 1 < len(lines):
                        next_line = lines[line_idx + 1].strip()
                        if next_line and len(next_line.split()) >= 2:
                            title = next_line
                    anchors.append({
                        "page_number": page_num,
                        "line_index": line_idx,
                        "line_text": line,
                        "title": title,
                        "document": doc,
                    })
        return anchors

    def _infer_service_title(self, documents: List[Document], filename: str) -> str:
        HEADER_NOISE = {
            "المملكة الأردنية", "المملكه الاردنيه", "وثيقة حكومية", "وثيقه حكوميه",
            "الصفحة", "الصفحه", "بوابة الحكومة", "بوابه الحكومه", "سند", "حقوق النشر",
        }
        # Check first heading or title line in text
        for doc in documents:
            for line in doc.text.split("\n"):
                clean = line.strip()
                if not clean or clean.startswith("["):
                    continue
                clean_no_digits = re.sub(r"^\d{4}\s+", "", clean)
                norm = normalize_arabic(clean_no_digits)
                if any(noise in norm for noise in HEADER_NOISE):
                    continue
                if any(kw in norm for kw in SECTION_KEYWORDS):
                    continue
                words = clean_no_digits.split()
                if 2 <= len(words) <= 18:
                    return clean_no_digits

        # Fallback to cleaned filename
        stem = Path(filename).stem
        clean_stem = re.sub(r"^[0-9a-fA-F]{8}_", "", stem)
        clean_stem = re.sub(r"^\d+_", "", clean_stem)
        return clean_stem.replace("_", " ").replace("-", " ").strip()

    def _build_single_service(
        self,
        documents: List[Document],
        document_id: str,
        filename: str,
        service_name: str,
        service_idx: int,
        review_status: str,
    ) -> ServiceRecord:
        clean_name = re.sub(r"[:：\-ـ\s]+$", "", service_name).strip()
        service_id = hashlib.sha256(
            f"{document_id}:{service_idx}:{clean_name}".encode("utf-8")
        ).hexdigest()[:16]

        pages = [doc.metadata.get("page_number") for doc in documents if doc.metadata.get("page_number")]
        start_page = min(pages) if pages else 1
        end_page = max(pages) if pages else 1

        chunker = ArabicGovernmentChunker(inject_heading_context=False)
        raw_sections = []
        section_order = 1

        for doc in documents:
            page_num = doc.metadata.get("page_number", 1)
            method = doc.metadata.get("extraction_method", "digital_pdf")
            sections = chunker.extract_sections(doc.text)
            if not sections:
                sections = [{"heading": None, "text": doc.text}]

            for sec in sections:
                heading = sec.get("heading")
                sec_text = sec.get("text", "").strip()
                if not sec_text:
                    continue

                sec_type = classify_section_type(heading)
                sec_id = f"{service_id}_sec_{section_order}"
                span = SourceSpan(
                    document_id=document_id,
                    filename=filename,
                    page_number=page_num,
                    section_title=heading,
                    extraction_method=method,
                )
                raw_sections.append({
                    "section_id": sec_id,
                    "service_id": service_id,
                    "section_type": sec_type,
                    "heading": heading,
                    "original_text": sec_text,
                    "normalized_search_text": normalize_arabic(sec_text),
                    "source_span": span.model_dump(),
                    "order": section_order,
                })
                section_order += 1

        warnings = []
        for doc in documents:
            if doc.metadata.get("warnings"):
                warnings.extend(doc.metadata["warnings"])

        return ServiceRecord(
            service_id=service_id,
            document_id=document_id,
            service_name=clean_name,
            aliases=generate_service_aliases(clean_name),
            start_page=start_page,
            end_page=end_page,
            raw_sections=raw_sections,
            extraction_warnings=warnings,
            review_status=review_status,
        )

    def _build_multi_services(
        self,
        documents: List[Document],
        document_id: str,
        filename: str,
        anchors: List[Dict[str, Any]],
    ) -> List[ServiceRecord]:
        services = []
        num_anchors = len(anchors)

        for i, anchor in enumerate(anchors, start=1):
            service_name = anchor["title"]
            clean_name = re.sub(r"[:：\-ـ\s]+$", "", service_name).strip()
            service_id = hashlib.sha256(
                f"{document_id}:{i}:{clean_name}".encode("utf-8")
            ).hexdigest()[:16]

            start_page = anchor["page_number"]
            end_page = (
                anchors[i]["page_number"]
                if i < num_anchors
                else (documents[-1].metadata.get("page_number", start_page))
            )

            # Collect matching document pages
            svc_docs = [
                d for d in documents
                if start_page <= d.metadata.get("page_number", start_page) <= end_page
            ]
            if not svc_docs:
                svc_docs = documents

            chunker = ArabicGovernmentChunker(inject_heading_context=False)
            raw_sections = []
            section_order = 1

            for doc in svc_docs:
                page_num = doc.metadata.get("page_number", start_page)
                method = doc.metadata.get("extraction_method", "digital_pdf")
                sections = chunker.extract_sections(doc.text)
                if not sections:
                    sections = [{"heading": None, "text": doc.text}]

                for sec in sections:
                    heading = sec.get("heading")
                    sec_text = sec.get("text", "").strip()
                    if not sec_text:
                        continue
                    sec_type = classify_section_type(heading)
                    sec_id = f"{service_id}_sec_{section_order}"
                    span = SourceSpan(
                        document_id=document_id,
                        filename=filename,
                        page_number=page_num,
                        section_title=heading,
                        extraction_method=method,
                    )
                    raw_sections.append({
                        "section_id": sec_id,
                        "service_id": service_id,
                        "section_type": sec_type,
                        "heading": heading,
                        "original_text": sec_text,
                        "normalized_search_text": normalize_arabic(sec_text),
                        "source_span": span.model_dump(),
                        "order": section_order,
                    })
                    section_order += 1

            services.append(
                ServiceRecord(
                    service_id=service_id,
                    document_id=document_id,
                    service_name=clean_name,
                    aliases=generate_service_aliases(clean_name),
                    start_page=start_page,
                    end_page=end_page,
                    raw_sections=raw_sections,
                    extraction_warnings=[],
                    review_status="reviewed",
                )
            )

        return services

    def _get_override_services(self, document_id: str, filename: str) -> Optional[List[Dict[str, Any]]]:
        if not self._overrides_data:
            return None
        items = self._overrides_data if isinstance(self._overrides_data, list) else self._overrides_data.get("overrides", [])
        for item in items:
            if item.get("document_id") == document_id or item.get("filename") == filename:
                return item.get("services")
        return None

    def _apply_overrides(
        self,
        documents: List[Document],
        document_id: str,
        filename: str,
        override_services: List[Dict[str, Any]],
    ) -> List[ServiceRecord]:
        services = []
        for idx, svc in enumerate(override_services, start=1):
            name = svc.get("service_name", f"Service {idx}")
            clean_name = re.sub(r"[:：\-ـ\s]+$", "", name).strip()
            service_id = hashlib.sha256(
                f"{document_id}:{idx}:{clean_name}".encode("utf-8")
            ).hexdigest()[:16]

            start_page = svc.get("start_page", 1)
            end_page = svc.get("end_page", len(documents))
            aliases = svc.get("aliases", generate_service_aliases(clean_name))

            svc_docs = [
                d for d in documents
                if start_page <= d.metadata.get("page_number", start_page) <= end_page
            ]
            if not svc_docs:
                svc_docs = documents

            chunker = ArabicGovernmentChunker(inject_heading_context=False)
            raw_sections = []
            section_order = 1

            for doc in svc_docs:
                page_num = doc.metadata.get("page_number", start_page)
                method = doc.metadata.get("extraction_method", "manual")
                sections = chunker.extract_sections(doc.text)
                if not sections:
                    sections = [{"heading": None, "text": doc.text}]

                for sec in sections:
                    heading = sec.get("heading")
                    sec_text = sec.get("text", "").strip()
                    if not sec_text:
                        continue
                    sec_type = classify_section_type(heading)
                    sec_id = f"{service_id}_sec_{section_order}"
                    span = SourceSpan(
                        document_id=document_id,
                        filename=filename,
                        page_number=page_num,
                        section_title=heading,
                        extraction_method=method,
                    )
                    raw_sections.append({
                        "section_id": sec_id,
                        "service_id": service_id,
                        "section_type": sec_type,
                        "heading": heading,
                        "original_text": sec_text,
                        "normalized_search_text": normalize_arabic(sec_text),
                        "source_span": span.model_dump(),
                        "order": section_order,
                    })
                    section_order += 1

            services.append(
                ServiceRecord(
                    service_id=service_id,
                    document_id=document_id,
                    service_name=clean_name,
                    aliases=aliases,
                    start_page=start_page,
                    end_page=end_page,
                    raw_sections=raw_sections,
                    extraction_warnings=[],
                    review_status="reviewed",
                )
            )

        return services


def service_records_to_chunks(
    services: List[ServiceRecord],
    default_source: Optional[str] = None,
) -> List[Chunk]:
    """Converts a collection of ServiceRecords into canonical Chunks with 100% metadata parity."""
    chunks = []
    for service in services:
        for sec in service.raw_sections:
            span = sec.get("source_span", {})
            heading = sec.get("heading")
            heading_path = [service.service_name]
            if heading:
                heading_path.append(heading)

            text = sec.get("original_text", "")
            # Inject service and heading breadcrumb header
            breadcrumb = " > ".join(heading_path)
            chunk_text = f"[{breadcrumb}]\n{text}"

            src_val = default_source or span.get("filename", "")

            metadata = {
                "document_id": service.document_id,
                "doc_id": service.document_id,
                "service_id": service.service_id,
                "service_name": service.service_name,
                "section_type": sec.get("section_type", "other"),
                "section_id": sec.get("section_id", ""),
                "filename": span.get("filename", ""),
                "source": src_val,
                "page_number": span.get("page_number"),
                "heading_path": heading_path,
                "extraction_method": span.get("extraction_method", "digital_pdf"),
                "order": sec.get("order", 0),
            }

            chk = Chunk(
                text=chunk_text,
                source=src_val,
                file_type="pdf" if "pdf" in str(src_val).lower() else "docx",
                chunk_index=sec.get("order", 0),
                chunking_strategy="arabic_service_section",
                metadata=metadata,
            )
            chunks.append(chk)
    return chunks
