"""Title and alias-aware service router for Jordan Government Services RAG.

Routes Arabic user queries to deterministic service_ids using exact title matching,
safe aliases, pronoun follow-up resolution, and token overlap margins,
preventing cross-service hallucination and fee confusion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from rag.ingestion.service_manifest import ServiceRecord, ServicesManifest, load_manifest
from rag.nlp.arabic import normalize_arabic, tokenize_arabic


FOLLOW_UP_PRONOUN_PATTERNS = [
    re.compile(r"^(?:و?كم|و?ما|و?ماهي|و?ما هي|و?ماذا عن)\s+(?:رسومها|شروطها|اوراقها|مستنداتها|اجراءاتها|مدتها|رسومه|شروطه|اوراقه|مستنداته|اجراءاته|مدته)\b", re.IGNORECASE),
    re.compile(r"^(?:هل\s+يمكن|كيف\s+يمكن)\s+(?:انجازها|التقديم\s+عليها|الحصول\s+عليها|تجديدها|اصدارها|انجازه|التقديم\s+عليه|الحصول\s+عليه|تجديده|اصداره)\b", re.IGNORECASE),
    re.compile(r"\b(?:لها|عنها|فيها|منها|بها|له|عنه|فيه|منه|به)\b", re.IGNORECASE),
]

COMPARISON_KEYWORDS = {
    "قارن", "قارن بين", "مقارنة", "مقارنه", "مقارنة بين", "مقارنه بين",
    "الفرق بين", "الفرق", "ما الفرق بين", "ما الفرق", "اوجه الشبه", "اوجه الاختلاف"
}

GENERIC_SERVICE_TITLE_WORDS = {
    "دليل", "اصدار", "إصدار", "تجديد", "خدمة", "خدمه", "طلب", "الحصول",
    "على", "في", "من", "الى", "إلى", "عن", "مع", "كافة", "جميع", "المملكة", "الاردنية",
    "الهاشمية", "معاملات", "معاملة", "معامله", "اجراءات", "إجراءات"
}


@dataclass
class RouteResult:
    routed_services: List[ServiceRecord]
    service_ids: Tuple[str, ...]
    confidence: float  # 0.0 to 1.0
    routing_reason: str  # exact_title | alias_match | token_overlap | follow_up_context | unscoped_fallback
    is_ambiguous: bool = False
    suggested_alternatives: List[str] = field(default_factory=list)

    @property
    def primary_service(self) -> Optional[ServiceRecord]:
        return self.routed_services[0] if self.routed_services else None


class ServiceRouter:
    """Routes Arabic queries to specific government services."""

    def __init__(self, services: Optional[List[ServiceRecord]] = None):
        self.services: List[ServiceRecord] = list(services) if services else []
        self._services_by_id: Dict[str, ServiceRecord] = {s.service_id: s for s in self.services}

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> ServiceRouter:
        manifest = load_manifest(manifest_path)
        if manifest:
            return cls(manifest.services)
        return cls([])

    def register_service(self, service: ServiceRecord) -> None:
        if service.service_id not in self._services_by_id:
            self.services.append(service)
            self._services_by_id[service.service_id] = service

    def route(
        self,
        query: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> RouteResult:
        if not self.services:
            return RouteResult(
                routed_services=[],
                service_ids=(),
                confidence=0.0,
                routing_reason="unscoped_fallback",
            )

        norm_query = normalize_arabic(query.strip())
        query_tokens = set(tokenize_arabic(norm_query))

        # 1. Check conversation history for follow-up resolution
        if history and self._is_follow_up(norm_query):
            prior_svc = self._resolve_from_history(history)
            if prior_svc:
                return RouteResult(
                    routed_services=[prior_svc],
                    service_ids=(prior_svc.service_id,),
                    confidence=0.90,
                    routing_reason="follow_up_context",
                )

        # 2. Check for multi-service comparison query
        is_comparison = False
        for kw in COMPARISON_KEYWORDS:
            if " " in kw:
                if kw in norm_query:
                    is_comparison = True
                    break
            elif kw in query_tokens:
                is_comparison = True
                break

        if is_comparison:
            matched_services = self._match_multiple_services(norm_query, query_tokens)
            if len(matched_services) >= 2:
                svc_ids = tuple(s.service_id for s in matched_services[:2])
                return RouteResult(
                    routed_services=matched_services[:2],
                    service_ids=svc_ids,
                    confidence=0.92,
                    routing_reason="comparison_query",
                )

        # 3. Exact and substring title matching
        for svc in self.services:
            norm_name = normalize_arabic(svc.service_name)
            if norm_name in norm_query or norm_query in norm_name:
                return RouteResult(
                    routed_services=[svc],
                    service_ids=(svc.service_id,),
                    confidence=0.98,
                    routing_reason="exact_title",
                )

        # 4. Alias matching
        for svc in self.services:
            for alias in svc.aliases:
                norm_alias = normalize_arabic(alias)
                if norm_alias and norm_alias in norm_query:
                    return RouteResult(
                        routed_services=[svc],
                        service_ids=(svc.service_id,),
                        confidence=0.95,
                        routing_reason="alias_match",
                    )

        # 5. Token overlap / lexical score ranking
        scored: List[Tuple[float, ServiceRecord]] = []
        for svc in self.services:
            score = self._compute_overlap_score(norm_query, query_tokens, svc)
            if score > 0.15:
                scored.append((score, svc))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return RouteResult(
                routed_services=[],
                service_ids=(),
                confidence=0.0,
                routing_reason="unscoped_fallback",
            )

        top_score, top_svc = scored[0]

        # Check margin over 2nd place
        if len(scored) > 1:
            second_score, second_svc = scored[1]
            margin = top_score - second_score
            if margin < 0.10 and top_score < 0.50:
                # Ambiguous query between two similar services
                return RouteResult(
                    routed_services=[top_svc],
                    service_ids=(top_svc.service_id,),
                    confidence=round(top_score, 2),
                    routing_reason="token_overlap",
                    is_ambiguous=True,
                    suggested_alternatives=[second_svc.service_name],
                )

        return RouteResult(
            routed_services=[top_svc],
            service_ids=(top_svc.service_id,),
            confidence=round(top_score, 2),
            routing_reason="token_overlap",
        )

    def _is_follow_up(self, norm_query: str) -> bool:
        return any(pat.search(norm_query) for pat in FOLLOW_UP_PRONOUN_PATTERNS)

    def _resolve_from_history(self, history: List[Any]) -> Optional[ServiceRecord]:
        for turn in reversed(history):
            if isinstance(turn, dict):
                svc_id = turn.get("service_id")
                if svc_id and svc_id in self._services_by_id:
                    return self._services_by_id[svc_id]
                q_text = (
                    turn.get("question")
                    or turn.get("user")
                    or (turn.get("content") if turn.get("role") == "user" else "")
                    or turn.get("content")
                    or ""
                )
            else:
                svc_id = getattr(turn, "service_id", None)
                if svc_id and svc_id in self._services_by_id:
                    return self._services_by_id[svc_id]
                q_text = getattr(turn, "content", "") or ""

            if q_text:
                norm_q = normalize_arabic(q_text)
                q_tokens = set(tokenize_arabic(norm_q))
                for svc in self.services:
                    norm_svc_name = normalize_arabic(svc.service_name)
                    if (
                        norm_svc_name in norm_q
                        or any(normalize_arabic(alias) in norm_q for alias in svc.aliases)
                        or self._compute_overlap_score(norm_q, q_tokens, svc) >= 0.20
                    ):
                        return svc
        return None

    def _match_multiple_services(self, norm_query: str, query_tokens: Set[str]) -> List[ServiceRecord]:
        matches = []
        for svc in self.services:
            norm_name = normalize_arabic(svc.service_name)
            svc_tokens = set(tokenize_arabic(norm_name))
            distinctive = svc_tokens - GENERIC_SERVICE_TITLE_WORDS
            if not distinctive:
                distinctive = svc_tokens

            if (
                norm_name in norm_query
                or any(normalize_arabic(alias) in norm_query for alias in svc.aliases)
                or (distinctive and len(distinctive.intersection(query_tokens)) >= 1 and self._compute_overlap_score(norm_query, query_tokens, svc) >= 0.25)
            ):
                matches.append(svc)
        return matches

    def _compute_overlap_score(
        self,
        norm_query: str,
        query_tokens: Set[str],
        svc: ServiceRecord,
    ) -> float:
        norm_name = normalize_arabic(svc.service_name)
        title_tokens = set(tokenize_arabic(norm_name))
        if not title_tokens:
            return 0.0

        distinctive = title_tokens - GENERIC_SERVICE_TITLE_WORDS
        if not distinctive:
            distinctive = title_tokens

        overlap = len(distinctive.intersection(query_tokens))
        jaccard = overlap / len(distinctive.union(query_tokens)) if distinctive else 0.0
        recall = overlap / len(distinctive) if distinctive else 0.0

        score = (recall * 0.8) + (jaccard * 0.2)

        # Check aliases for boost
        for alias in svc.aliases:
            alias_tokens = set(tokenize_arabic(normalize_arabic(alias))) - GENERIC_SERVICE_TITLE_WORDS
            if alias_tokens:
                alias_overlap = len(alias_tokens.intersection(query_tokens))
                alias_recall = alias_overlap / len(alias_tokens)
                if alias_recall > score:
                    score = alias_recall

        return min(round(score, 3), 1.0)
