"""High-Precision Arabic Intent Router for Jordan Civil Status & Passports RAG."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from rag.nlp.arabic import normalize_arabic, tokenize_arabic
from src.hackathon.corpus import HackathonCorpus, ServiceDocument


OUT_OF_SCOPE_KEYWORDS = {
    "طيران", "تذكرة", "تذاكر", "دبي", "فندق", "حجز", "فيزا شنغن", "سياحة",
    "طقس", "جامعة", "جامعه", "جامعي", "جامعية", "جامعيه", "جامعات", "شهادة", "شهادات",
    "تصديق", "تعليم", "تعليم عالي", "مدرسة", "مدرسه", "مدارس", "امتحان", "معدل", "توجيهي", "قبول موحد",
    "ضريبة الدخل", "رخصة قيادة", "مخالفات السير", "ترخيص سيارات",
    "ضمان اجتماعي", "تقاعد", "شراء بيت", "إيجار", "وظيفة", "وظائف", "ديوان الخدمة"
}

PRONOUN_FOLLOWUP_INDICATORS = [
    re.compile(r"^(?:و?هل|و?بقدر|و?ممكن|و?كيف|و?وين|و?كم|و?قديش|و?شو|و?ماذا)\s+", re.IGNORECASE),
    re.compile(r"\b(?:لها|عنها|فيها|منها|بها|له|عنه|فيه|منه|به|الطلب|المعاملة)\b", re.IGNORECASE),
]


@dataclass
class RouteTarget:
    doc_type: str  # passport | family_book | id_card
    situation: str  # first_issue | renewal | lost | damaged
    section_keys: List[str]  # e.g. ['documents'], ['fees'], ['sla'], ['locations']


@dataclass
class RouteDecision:
    targets: List[RouteTarget]
    is_out_of_scope: bool = False
    is_unclear: bool = False
    refusal_reason: str = ""


class IntentRouter:
    """Routes Arabic queries to exact (doc_type, situation, section) targets."""

    def __init__(self, corpus: HackathonCorpus):
        self.corpus = corpus

    def route(
        self,
        question: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> RouteDecision:
        norm_q = normalize_arabic(question)
        q_tokens = set(tokenize_arabic(norm_q))

        # 1. Out of scope check
        for kw in OUT_OF_SCOPE_KEYWORDS:
            if kw in norm_q or kw in q_tokens:
                # Unless it also explicitly mentions our core civil documents
                if self._detect_doc_type(norm_q) is None:
                    return RouteDecision(
                        targets=[],
                        is_out_of_scope=True,
                        refusal_reason="out_of_scope",
                    )

        # 2. Check for multi-clause or composite multi-service inquiries
        clauses = [s.strip() for s in re.split(r'[\.\?\!\u061f\n]+|;\s*', question) if s.strip()]
        if len(clauses) == 1 and "،" in question:
            sub_parts = [p.strip() for p in question.split("،") if p.strip()]
            if sum(1 for p in sub_parts if self._detect_doc_type(normalize_arabic(p))) >= 2:
                clauses = sub_parts

        global_secs = self._detect_sections(norm_q)

        if len(clauses) > 1:
            multi_targets = []
            seen_pairs = set()
            for clause in clauses:
                norm_c = normalize_arabic(clause)
                doc = self._detect_doc_type(norm_c)
                if doc:
                    sit = self._detect_situation(norm_c) or "renewal"
                    secs = self._detect_sections(norm_c) or global_secs or ["fees", "conditions", "notes"]
                    pair = (doc, sit)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        multi_targets.append(RouteTarget(doc_type=doc, situation=sit, section_keys=secs))
            if len(multi_targets) >= 2:
                return RouteDecision(targets=multi_targets)

        # 3. Check for single-sentence multi-service comparison (e.g. chat-04-1)
        comparison_targets = self._check_comparison(norm_q)
        if comparison_targets:
            return RouteDecision(targets=comparison_targets)

        # 4. Detect target document type
        doc_type = self._detect_doc_type(norm_q)

        # 5. Detect situation (renewal, first_issue, lost, damaged)
        situation = self._detect_situation(norm_q)

        # 6. Check history for follow-up resolution if missing document or situation
        if history and (doc_type is None or situation is None):
            prior_doc, prior_sit = self._resolve_from_history(history)
            if doc_type is None:
                doc_type = prior_doc
            if situation is None:
                situation = prior_sit or "renewal"

        # Defaults if only document is specified
        if doc_type and situation is None:
            situation = "renewal"  # Most common default citizen action

        if doc_type is None:
            # If the user asks for renewal/issuance/fees/lost without mentioning which document, clarify!
            if any(k in norm_q for k in ["اجدد", "أجدد", "تجديد", "اطلع", "أطلع", "اصدار", "إصدار", "بدل فاقد", "بدل تالف", "معاملة", "الوثيقة"]):
                return RouteDecision(targets=[], is_unclear=True)
            # Otherwise, since no civil document was mentioned, it's out of scope
            return RouteDecision(targets=[], is_out_of_scope=True)

        # 7. Detect target section(s)
        sections = self._detect_sections(norm_q)
        if not sections:
            sections = ["conditions", "documents", "fees"]  # Comprehensive fallback

        target = RouteTarget(
            doc_type=doc_type,
            situation=situation,
            section_keys=sections,
        )
        return RouteDecision(targets=[target])

    def _detect_doc_type(self, norm_q: str) -> Optional[str]:
        if any(w in norm_q for w in ["جواز", "جوازات", "جوازي", "جوازه", "جوازها", "جوازك", "باسبور", "باسبورت", "سفر"]):
            return "passport"
        if any(w in norm_q for w in ["عائلة", "عائله", "عيلة", "عيله", "دفتر"]):
            return "family_book"
        if any(w in norm_q for w in [
            "بطاقة ذكية", "بطاقه ذكيه", "البطاقة الذكية", "البطاقه الذكيه",
            "هوية", "هويه", "الهوية", "الهويه", "هويته", "هويتها", "هويتي", "هويتهم", "هويتك",
            "بطاقة شخصية", "بطاقه شخصيه", "بطاقة", "بطاقه", "بطاقتي", "بطاقتها", "بطاقته"
        ]):
            return "id_card"
        return None

    def _detect_situation(self, norm_q: str) -> Optional[str]:
        if any(w in norm_q for w in ["تالف", "بدل تالف", "اهترى", "مهترئ", "ممزوع", "مغسول", "غسيل", "غسالة", "غساله", "تلف", "تلفت"]):
            return "damaged"
        if any(w in norm_q for w in ["فاقد", "بدل فاقد", "ضاع", "ضاعت", "ضيع", "ضيّع", "فقدت", "فقدان", "سرق", "مسروق"]):
            return "lost"
        if any(w in norm_q for w in ["تجديد", "اجدد", "أجدد", "تجديده", "تجديدها", "خلص", "منتهي", "منتهية", "انتهاء"]):
            return "renewal"
        if any(w in norm_q for w in ["اول مرة", "أول مرة", "اول مره", "أول مره", "اصدار اول", "إصدار أول", "غير مسجلين"]) or re.search(r"\bجديد(?:ة|ه)?\b", norm_q):
            return "first_issue"
        return None

    def _detect_sections(self, norm_q: str) -> List[str]:
        sections = []
        # SLA
        if any(w in norm_q for w in [
            "يستغرق", "تستغرق", "بتستغرق", "كم وقت", "كم مدة", "كم مده", "المدة", "المدة الزمنية",
            "الزمن", "كم بدها", "كم بدها وقت", "كم ياخذ", "كم يأخذ", "دقيقة", "دقائق", "ساعة", "ساعات",
            "بتاخذ", "تاخذ", "بتوخذ", "توخذ", "يوخذ", "ياخذ", "تأخذ"
        ]):
            sections.append("sla")
        # Locations / Channels
        if any(w in norm_q for w in ["وين", "اين", "أين", "مكان", "اماكن", "أماكن", "سفارة", "سفاره", "السفارة", "السفاره", "قنصلية", "قنصليه", "برا البلد", "خارج الاردن", "خارج الأردن"]):
            sections.append("locations")
        # Documents
        if any(w in norm_q for w in ["اوراق", "أوراق", "وثائق", "مستندات", "شو بيلزمني", "شو اجيب", "شو أحتاج", "احتاج", "صورة شخصية", "صور شخصية", "صورة", "صور"]):
            sections.append("documents")
        # Fees
        if any(w in norm_q for w in ["رسوم", "كم بكلف", "بتكلف", "قديش بدفع", "كم ادفع", "كم أدفع", "سعر", "دينار", "دنانير", "تكلفة", "غرامة", "أغلى", "اغلى"]):
            sections.append("fees")
        # Conditions / Eligibility
        if any(w in norm_q for w in ["شروط", "يحق", "موافقة", "موافقه", "ولي الامر", "ولي الأمر", "عمر", "سن", "قاصر", "زوجها", "رب الاسرة", "رب الأسرة", "توفي", "وفاة", "وفاه"]):
            sections.append("conditions")
            sections.append("documents")
            sections.append("notes")
        # Notes (Urgent desks, special cases)
        if any(w in norm_q for w in ["مستعجل", "المستعجلة", "مستعجله", "مقدسي", "مقدسية", "ملاحظات", "كفالة", "كفاله", "عدلية", "عدليه"]):
            if "notes" not in sections:
                sections.append("notes")

        return sections

    def _check_comparison(self, norm_q: str) -> Optional[List[RouteTarget]]:
        is_comparison = any(w in norm_q for w in [
            "ايهما", "أيهما", "الفرق", "مقارنة", "مقارنه", "ولا", "مين أغلى", "مين اغلى",
            "مين أسرع", "مين اسرع", "مين ارخص", "مين أرخص"
        ])

        # Check for multiple situations (damaged, lost, renewal, first_issue)
        detected_situations = []
        if any(w in norm_q for w in ["تالف", "بدل تالف"]):
            detected_situations.append("damaged")
        if any(w in norm_q for w in ["فاقد", "بدل فاقد", "ضيع"]):
            detected_situations.append("lost")
        if any(w in norm_q for w in ["تجديد", "اجدد", "أجدد", "تجديده"]):
            detected_situations.append("renewal")
        if any(w in norm_q for w in ["اول مرة", "أول مرة", "اول مره", "أول مره", "اصدار اول", "إصدار أول"]):
            detected_situations.append("first_issue")

        doc = self._detect_doc_type(norm_q)

        # Case 1: Same document, multiple situations (e.g. passport damaged vs passport lost)
        if doc and len(detected_situations) >= 2 and is_comparison:
            secs = self._detect_sections(norm_q) or ["fees", "conditions"]
            return [
                RouteTarget(doc_type=doc, situation=sit, section_keys=secs)
                for sit in detected_situations
            ]

        # Case 2: Across different documents (e.g. id_card first_issue vs passport renewal)
        has_id = any(w in norm_q for w in ["بطاقة", "بطاقه", "هوية", "هويه"])
        has_passport = any(w in norm_q for w in ["جواز", "باسبور"])
        has_family = any(w in norm_q for w in ["دفتر", "عائلة", "عيلة"])

        matched_docs = []
        if has_id:
            sit = "first_issue" if any(w in norm_q for w in ["اول", "أول"]) else "renewal"
            matched_docs.append(("id_card", sit))
        if has_passport:
            sit = "renewal" if any(w in norm_q for w in ["تجديد", "تجديده"]) else "first_issue"
            matched_docs.append(("passport", sit))
        if has_family:
            sit = "renewal" if any(w in norm_q for w in ["تجديد"]) else "first_issue"
            matched_docs.append(("family_book", sit))

        if len(matched_docs) >= 2:
            secs = self._detect_sections(norm_q) or ["documents", "fees"]
            targets = [
                RouteTarget(doc_type=d, situation=s, section_keys=secs)
                for d, s in matched_docs
            ]
            return targets

        return None

    def _resolve_from_history(self, history: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        for turn in reversed(history):
            q_text = turn.get("question") or turn.get("content") or ""
            if not q_text:
                continue
            norm = normalize_arabic(q_text)
            doc = self._detect_doc_type(norm)
            sit = self._detect_situation(norm)
            if doc or sit:
                return doc, sit
        return None, None
