"""Canonical service manifest models and persistence for Jordan Government Services RAG.

Defines typed schemas for SourceSpan, ServiceSection, ServiceRecord, and ServicesManifest,
matching the hackathon architectural contract.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from rag.nlp.arabic import normalize_arabic


class SourceSpan(BaseModel):
    document_id: str  # SHA-256 of original input file
    filename: str
    page_number: Optional[int] = None  # 1-indexed PDF page; None when unavailable
    section_title: Optional[str] = None
    extraction_method: str = "digital_pdf"  # digital_pdf | docx | ocr | text | manual


class ServiceSection(BaseModel):
    section_id: str
    service_id: str
    section_type: str  # requirements | eligibility | fees | steps | processing_time | channels | exceptions | other
    heading: Optional[str] = None
    original_text: str
    normalized_search_text: str
    source_span: SourceSpan
    order: int


class ServiceRecord(BaseModel):
    service_id: str  # Deterministic hash(document_id + boundary anchor)
    document_id: str
    service_name: str
    aliases: List[str] = Field(default_factory=list)
    organization: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    raw_sections: List[Dict[str, Any]] = Field(default_factory=list)
    extraction_warnings: List[str] = Field(default_factory=list)
    review_status: str = "needs_review"  # reviewed | needs_review

    @property
    def sections(self) -> List[Dict[str, Any]]:
        return self.raw_sections


class ServicesManifest(BaseModel):
    services_count: int
    generated_at: str
    services: List[ServiceRecord] = Field(default_factory=list)


def classify_section_type(heading: Optional[str]) -> str:
    """Classifies a section heading into standard government service categories."""
    if not heading:
        return "other"

    norm = normalize_arabic(heading.lower())

    if any(k in norm for k in ("رسوم", "المقابل المالي", "تكلفه", "سعر", "ثمن")):
        return "fees"
    if any(k in norm for k in ("وثائق", "مستندات", "اوراق", "اوراق مطلوبه", "متطلبات")):
        return "requirements"
    if any(k in norm for k in ("شروط", "معايير", "فئات", "مستفيدون", "اهليه", "استحقاق")):
        return "eligibility"
    if any(k in norm for k in ("اجراءات", "خطوات", "مسار", "كيفيه الحصول")):
        return "steps"
    if any(k in norm for k in ("مده", "وقت", "ساعات", "ايام", "فتره انجاز")):
        return "processing_time"
    if any(k in norm for k in ("قنوات", "مكان", "مواقع", "سند", "مراكز تقديم")):
        return "channels"
    if any(k in norm for k in ("استثناءات", "حالات خاصه", "ملاحظات", "تنبيهات", "ملاحظه")):
        return "exceptions"

    return "other"


def generate_service_aliases(service_name: str) -> List[str]:
    """Generates conservative, safe aliases without inventing facts or confusing services."""
    aliases = set()
    clean_name = service_name.strip()
    norm = normalize_arabic(clean_name)

    # 1. Strip leading "خدمة" or "بطاقة خدمة" or "دليل"
    for prefix in ("خدمه ", "بطاقه خدمه ", "دليل خدمه ", "دليل "):
        if norm.startswith(prefix):
            unprefixed = clean_name[len(prefix):].strip()
            if unprefixed:
                aliases.add(unprefixed)

    # 2. Add common Jordanian colloquial / official phrasing variations
    if "البطاقة الشخصية" in clean_name or "البطاقه الشخصيه" in norm:
        aliases.update(["الهوية الشخصية", "الهوية الذكية", "الهوية", "هوية", "بطاقة شخصية", "الهويه الشخصيه", "الهويه"])
    if "جواز السفر" in clean_name:
        aliases.update(["جواز سفر", "جواز", "الجواز"])
    if "دفتر العائلة" in clean_name or "دفتر العائله" in norm:
        aliases.update(["دفتر عائلة", "دفتر عائله", "دفتر العيلة", "دفتر عيلة"])
    if "رخص القيادة" in clean_name or "رخصه القياده" in norm:
        aliases.update(["رخصة القيادة", "رخصه السواقه", "رخصة السواقة", "رخصة قيادة", "رخصة سواقة"])
    if "ترخيص" in clean_name and "المركبات" in clean_name:
        aliases.update(["ترخيص المركبات", "ترخيص المركبة", "ترخيص السيارات", "ترخيص سيارة"])
    if "الأبنية" in clean_name or "الابنيه" in norm:
        aliases.update(["ترخيص الأبنية", "ترخيص البناء", "ترخيص بناء", "رخصة بناء", "إذن إشغال", "اذن اشغال"])
    if "عدم المحكومية" in clean_name or "عدم المحكوميه" in norm:
        aliases.update(["عدم محكومية", "شهادة عدم محكومية", "عدم محكوميه"])
    if "رخص المهن" in clean_name:
        aliases.update(["رخصة المهن", "ترخيص المهن", "رخصة تجارية", "ترخيص تجاري"])
    if "الاشتراك الاختياري" in clean_name or "التعطل" in clean_name:
        aliases.update(["الضمان الاجتماعي", "الضمان", "بدل التعطل", "اشتراك الضمان"])
    if "التأمين الصحي" in clean_name or "التامين الصحي" in norm:
        aliases.update(["التأمين الصحي", "تامين صحي", "بطاقة التأمين الصحي"])

    if "بدل فاقد" in clean_name and "هوية" not in clean_name and "جواز" not in clean_name:
        aliases.add(f"{clean_name} للبطاقة الشخصية")

    return sorted([a for a in aliases if a and a != service_name])


def save_manifest(manifest: ServicesManifest, file_path: Path) -> None:
    """Saves the services manifest to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, ensure_ascii=False, indent=2)


def load_manifest(file_path: Path) -> Optional[ServicesManifest]:
    """Loads the services manifest from a JSON file if present."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ServicesManifest.model_validate(data)
    except Exception:
        return None
