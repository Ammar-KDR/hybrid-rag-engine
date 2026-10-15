"""Hackathon Corpus Loader & Section Parser for Jordan Civil Status & Passports Department."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SERVICE_REGISTRY: Dict[str, Dict[str, str]] = {
    "passport_first_issue.txt": {
        "service_key": "passport_first_issue",
        "doc_type": "passport",
        "situation": "first_issue",
        "title": "إصدار جواز السفر لأول مرة",
        "alt_title": "جواز سفر لأول مرة",
    },
    "passport_renewal.txt": {
        "service_key": "passport_renewal",
        "doc_type": "passport",
        "situation": "renewal",
        "title": "تجديد جواز السفر",
        "alt_title": "تجديد جواز السفر العادي",
    },
    "passport_lost.txt": {
        "service_key": "passport_lost",
        "doc_type": "passport",
        "situation": "lost",
        "title": "جواز سفر بدل فاقد",
        "alt_title": "جواز سفر بدل فاقد",
    },
    "passport_damaged.txt": {
        "service_key": "passport_damaged",
        "doc_type": "passport",
        "situation": "damaged",
        "title": "جواز سفر بدل تالف",
        "alt_title": "جواز سفر بدل تالف",
    },
    "family_book_first_issue.txt": {
        "service_key": "family_book_first_issue",
        "doc_type": "family_book",
        "situation": "first_issue",
        "title": "إصدار دفتر العائلة لأول مرة",
        "alt_title": "دفتر عائلة لأول مرة",
    },
    "family_book_renewal.txt": {
        "service_key": "family_book_renewal",
        "doc_type": "family_book",
        "situation": "renewal",
        "title": "تجديد دفتر العائلة",
        "alt_title": "تجديد دفتر عائلة",
    },
    "family_book_lost.txt": {
        "service_key": "family_book_lost",
        "doc_type": "family_book",
        "situation": "lost",
        "title": "دفتر عائلة بدل فاقد",
        "alt_title": "دفتر عائلة بدل فاقد",
    },
    "family_book_damaged.txt": {
        "service_key": "family_book_damaged",
        "doc_type": "family_book",
        "situation": "damaged",
        "title": "دفتر عائلة بدل تالف",
        "alt_title": "دفتر عائلة بدل تالف",
    },
    "id_card_first_issue.txt": {
        "service_key": "id_card_first_issue",
        "doc_type": "id_card",
        "situation": "first_issue",
        "title": "إصدار البطاقة الذكية لأول مرة",
        "alt_title": "بطاقة ذكية لأول مرة",
    },
    "id_card_renewal.txt": {
        "service_key": "id_card_renewal",
        "doc_type": "id_card",
        "situation": "renewal",
        "title": "تجديد البطاقة الذكية",
        "alt_title": "تجديد بطاقة الأحوال المدنية الذكية",
    },
    "id_card_lost.txt": {
        "service_key": "id_card_lost",
        "doc_type": "id_card",
        "situation": "lost",
        "title": "بطاقة ذكية بدل فاقد",
        "alt_title": "بطاقة الأحوال المدنية الذكية بدل فاقد",
    },
    "id_card_damaged.txt": {
        "service_key": "id_card_damaged",
        "doc_type": "id_card",
        "situation": "damaged",
        "title": "بطاقة ذكية بدل تالف",
        "alt_title": "بطاقة الأحوال المدنية الذكية بدل تالف",
    },
}

SECTION_SPEC: List[Tuple[str, str, str]] = [
    ("beneficiaries", "الفئة المستفيدة", "الفئة المستفيدة"),
    ("locations", "أماكن تقديم الخدمة", "أماكن تقديم الخدمة"),
    ("conditions", "شروط تقديم الخدمة", "شروط تقديم الخدمة"),
    ("documents", "الوثائق المطلوبة للحصول على الخدمة", "الوثائق المطلوبة"),
    ("procedures", "إجراءات تقديم الخدمة", "إجراءات تقديم الخدمة"),
    ("sla", "الزمن المستغرق لتقديم الخدمة", "الزمن المستغرق لتقديم الخدمة"),
    ("partners", "شركاء الخدمة", "شركاء الخدمة"),
    ("notes", "ملاحظات", "ملاحظات"),
    ("fees", "الرسوم", "الرسوم"),
]


@dataclass
class ServiceSection:
    key: str
    header_name: str
    display_header: str
    content: str
    context_string: str


@dataclass
class ServiceDocument:
    service_key: str
    doc_type: str
    situation: str
    title: str
    filename: str
    sections: Dict[str, ServiceSection]


class HackathonCorpus:
    """Manages the 12 parsed official service documents."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or self._find_data_dir()
        self.documents: Dict[str, ServiceDocument] = {}
        self._by_type_and_sit: Dict[Tuple[str, str], ServiceDocument] = {}
        self._load_all()

    def _find_data_dir(self) -> Path:
        candidates = [
            Path("data"),
            Path("participant_pack/data"),
            Path("data/hackathon_live_pack/participant_pack/data"),
        ]
        for c in candidates:
            if c.exists() and any(c.glob("*.txt")):
                return c
        return Path("data")

    def _load_all(self) -> None:
        for filename, meta in SERVICE_REGISTRY.items():
            fpath = self.data_dir / filename
            if not fpath.exists():
                alt_path = Path("data/hackathon_live_pack/participant_pack/data") / filename
                if alt_path.exists():
                    fpath = alt_path

            if not fpath.exists():
                continue

            doc = self._parse_file(fpath, meta)
            self.documents[meta["service_key"]] = doc
            self._by_type_and_sit[(meta["doc_type"], meta["situation"])] = doc

    def _parse_file(self, filepath: Path, meta: Dict[str, str]) -> ServiceDocument:
        text = filepath.read_text(encoding="utf-8")
        
        # Strip header website navigation lines (everything before first section header)
        lines = text.splitlines()
        start_idx = 0
        for i, line in enumerate(lines):
            if "الفئة المستفيدة" in line:
                start_idx = i
                break
        body = "\n".join(lines[start_idx:])

        # Locate every section in order
        positions = []
        for key, raw_header, display_header in SECTION_SPEC:
            # Match header at start of line
            m = re.search(rf"^(?:[\s\t]*){re.escape(raw_header)}[\s\t]*", body, re.MULTILINE)
            if not m and key == "documents":
                m = re.search(r"^(?:[\s\t]*)الوثائق المطلوبة[\s\t]*", body, re.MULTILINE)
            if m:
                positions.append((m.start(), m.end(), key, raw_header, display_header))

        positions.sort(key=lambda x: x[0])

        sections: Dict[str, ServiceSection] = {}
        for idx, (h_start, h_end, key, raw_header, display_header) in enumerate(positions):
            next_start = positions[idx + 1][0] if idx + 1 < len(positions) else len(body)
            raw_content = body[h_end:next_start].strip()
            
            # Clean leading colons or tabs
            cleaned_content = re.sub(r"^[\s\t\:\-]+", "", raw_content).strip()
            
            # Formulate the exact canonical context string required by the benchmark:
            # "{service_title} - {display_header}: {content}"
            # e.g.: "تجديد دفتر العائلة - الزمن المستغرق لتقديم الخدمة: 45 دقيقة"
            ctx_str = f"{meta['title']} - {display_header}: {cleaned_content}"

            sections[key] = ServiceSection(
                key=key,
                header_name=raw_header,
                display_header=display_header,
                content=cleaned_content,
                context_string=ctx_str,
            )

        return ServiceDocument(
            service_key=meta["service_key"],
            doc_type=meta["doc_type"],
            situation=meta["situation"],
            title=meta["title"],
            filename=filepath.name,
            sections=sections,
        )

    def get_service(self, doc_type: str, situation: str) -> Optional[ServiceDocument]:
        return self._by_type_and_sit.get((doc_type, situation))

    def get_by_key(self, service_key: str) -> Optional[ServiceDocument]:
        return self.documents.get(service_key)
