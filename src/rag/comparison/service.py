import json
import re
import urllib.request
from typing import Optional

from rag.api.schemas.ask import EvidenceRef
from rag.api.schemas.compare import (
    CompareResponse,
    ComparisonRelationship,
    DocumentClaim,
)
from rag.config import settings
from rag.ingestion.registry import DocumentRegistry
from rag.pipeline import RAGPipeline
from rag.retrieval.model import RetrievalFilter
from rag.nlp.arabic import is_arabic_text


class DocumentComparisonService:
    def __init__(
        self,
        pipeline: RAGPipeline,
        registry: DocumentRegistry,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.pipeline = pipeline
        self.registry = registry
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def _build_evidence_ref(self, chunk, ref_idx: int, doc_id: str, filename: str) -> EvidenceRef:
        meta = getattr(chunk, "metadata", {}) or {}
        return EvidenceRef(
            reference=ref_idx,
            chunk_id=chunk.chunk_id,
            document_id=doc_id,
            filename=filename,
            source=meta.get("source") or getattr(chunk, "source", ""),
            text=chunk.text,
            file_type=meta.get("file_type") or getattr(chunk, "file_type", None),
            page_number=meta.get("page_number") or getattr(chunk, "page_number", None),
            heading_path=meta.get("heading_path") or getattr(chunk, "heading_path", None),
            final_score=getattr(chunk, "final_score", None),
        )

    def compare(
        self,
        document_a_id: str,
        document_b_id_val: str,
        topic: str,
    ) -> CompareResponse:
        rec_a = self.registry.get(document_a_id) or {}
        rec_b = self.registry.get(document_b_id_val) or {}

        filename_a = rec_a.get("filename", f"Doc {document_a_id[:8]}")
        filename_b = rec_b.get("filename", f"Doc {document_b_id_val[:8]}")

        # Step 1: Scoped retrieval on Document A
        filter_a = RetrievalFilter(document_ids=(document_a_id,))
        cand_a = self.pipeline.retriever.retrieve(query=topic, top_k=5, filter=filter_a)
        chunks_a = (
            self.pipeline.reranker.rerank(query=topic, candidates=cand_a)[:3]
            if cand_a
            else []
        )

        # Step 2: Scoped retrieval on Document B
        filter_b = RetrievalFilter(document_ids=(document_b_id_val,))
        cand_b = self.pipeline.retriever.retrieve(query=topic, top_k=5, filter=filter_b)
        chunks_b = (
            self.pipeline.reranker.rerank(query=topic, candidates=cand_b)[:3]
            if cand_b
            else []
        )

        evidence_a = [
            self._build_evidence_ref(c, idx, document_a_id, filename_a)
            for idx, c in enumerate(chunks_a, start=1)
        ]
        evidence_b = [
            self._build_evidence_ref(c, idx, document_b_id_val, filename_b)
            for idx, c in enumerate(chunks_b, start=1)
        ]

        is_ar_topic = is_arabic_text(topic) or is_arabic_text(filename_a) or is_arabic_text(filename_b)

        # Step 3: Check sufficiency
        if not chunks_a or not chunks_b:
            missing = []
            if not chunks_a:
                missing.append(filename_a)
            if not chunks_b:
                missing.append(filename_b)

            if is_ar_topic:
                summary_text = f"الأدلة المتاحة حول '{topic}' غير كافية في: {', '.join(missing)}."
                res_notes = "يرجى تزويد النظام بوثائق رسمية تغطي هذا الموضوع لتمكين التدقيق الآلي للتعارض."
                claim_fallback = "لم يتم العثور على نصوص كافية."
            else:
                summary_text = f"Insufficient evidence on '{topic}' found in: {', '.join(missing)}."
                res_notes = "Provide documents with explicit coverage of this topic to enable automated conflict analysis."
                claim_fallback = "No relevant passages found."

            return CompareResponse(
                topic=topic,
                relationship=ComparisonRelationship.INSUFFICIENT_EVIDENCE,
                summary=summary_text,
                document_a=DocumentClaim(
                    document_id=document_a_id,
                    filename=filename_a,
                    claim=chunks_a[0].text[:200] if chunks_a else claim_fallback,
                    evidence=evidence_a,
                ),
                document_b=DocumentClaim(
                    document_id=document_b_id_val,
                    filename=filename_b,
                    claim=chunks_b[0].text[:200] if chunks_b else claim_fallback,
                    evidence=evidence_b,
                ),
                resolution_notes=res_notes,
                confidence="low",
            )

        # Step 4: Ollama Structured Comparison Analysis
        text_a = "\n\n".join(f"[Passage A{i}]: {c.text}" for i, c in enumerate(chunks_a, start=1))
        text_b = "\n\n".join(f"[Passage B{i}]: {c.text}" for i, c in enumerate(chunks_b, start=1))

        system_prompt = (
            "You are a rigorous policy and technical documentation auditor.\n"
            "Your task is to analyze evidence from two documents regarding a specific topic, "
            "and determine their factual relationship with zero hallucination.\n\n"
            "RELATIONSHIP CATEGORIES:\n"
            "- 'agreement': Both documents state the same requirements, policies, or facts.\n"
            "- 'scope_or_version_difference': The documents have different rules because they apply to different scopes, versions, tiers, or effective dates.\n"
            "- 'possible_conflict': The documents make contradictory, incompatible factual statements on the same exact scope.\n"
            "- 'insufficient_evidence': The passages do not clearly answer the topic.\n\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "relationship": "agreement" | "scope_or_version_difference" | "possible_conflict" | "insufficient_evidence",\n'
            '  "summary": "Brief 1-2 sentence overview of the relationship",\n'
            '  "doc_a_claim": "Specific statement made by Document A on this topic",\n'
            '  "doc_a_scope": "Scope, tier, or version conditions in Document A or null",\n'
            '  "doc_b_claim": "Specific statement made by Document B on this topic",\n'
            '  "doc_b_scope": "Scope, tier, or version conditions in Document B or null",\n'
            '  "resolution_notes": "How a decision maker or engineer should resolve or interpret this difference",\n'
            '  "confidence": "high" | "medium" | "low"\n'
            "}"
        )

        if is_ar_topic:
            system_prompt += (
                "\n\nCRITICAL LANGUAGE INSTRUCTION:\n"
                "The topic and documents are in Arabic. You MUST generate all text content in the JSON "
                "('summary', 'doc_a_claim', 'doc_b_claim', 'resolution_notes') in formal, authoritative Arabic (لغة عربية فصحى رسمية). "
                "The JSON keys and 'relationship' values must remain in standard English."
            )

        user_content = (
            f"Topic: {topic}\n\n"
            f"--- EVIDENCE FROM DOCUMENT A ({filename_a}) ---\n"
            f"{text_a}\n\n"
            f"--- EVIDENCE FROM DOCUMENT B ({filename_b}) ---\n"
            f"{text_b}\n\n"
            "JSON Analysis:"
        )

        try:
            clean_url = self.base_url.rstrip("/")
            if clean_url.endswith("/v1"):
                clean_url = clean_url[:-3]

            raw_json = ""
            # Try native Ollama /api/chat first with think=False
            try:
                import requests
                native_payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "think": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 600,
                    },
                    "keep_alive": -1,
                    "stream": False,
                }
                resp = requests.post(f"{clean_url}/api/chat", json=native_payload, timeout=45)
                if resp.status_code == 200:
                    raw_json = resp.json().get("message", {}).get("content", "").strip()
            except Exception:
                pass

            if not raw_json:
                chat_url = f"{self.base_url}/chat/completions"
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 600,
                }
                req = urllib.request.Request(
                    chat_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "ConflictDetective"},
                )
                with urllib.request.urlopen(req, timeout=30.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_json = data["choices"][0]["message"]["content"].strip()

            # Clean <think> tags if present
            raw_json = re.sub(r"<think>.*?</think>", "", raw_json, flags=re.DOTALL).strip()
            # Clean JSON markdown fences if present
            raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json, flags=re.MULTILINE)
            raw_json = re.sub(r"```$", "", raw_json, flags=re.MULTILINE).strip()

            parsed = json.loads(raw_json)

            rel_str = str(parsed.get("relationship", "possible_conflict")).lower().replace(" ", "_")
            if rel_str not in [e.value for e in ComparisonRelationship]:
                rel_str = "possible_conflict"

            default_summary = (
                f"تمت مقارنة موضوع '{topic}' بدقة بين الوثيقتين."
                if is_ar_topic
                else "Document comparison completed."
            )
            default_res_notes = (
                "يوصى بمراجعة النصوص المرجعية المعتمدة قبل التطبيق."
                if is_ar_topic
                else "Review primary documents before enforcement."
            )

            return CompareResponse(
                topic=topic,
                relationship=ComparisonRelationship(rel_str),
                summary=parsed.get("summary", default_summary),
                document_a=DocumentClaim(
                    document_id=document_a_id,
                    filename=filename_a,
                    claim=parsed.get("doc_a_claim", chunks_a[0].text[:200]),
                    evidence=evidence_a,
                    scope_notes=parsed.get("doc_a_scope"),
                ),
                document_b=DocumentClaim(
                    document_id=document_b_id_val,
                    filename=filename_b,
                    claim=parsed.get("doc_b_claim", chunks_b[0].text[:200]),
                    evidence=evidence_b,
                    scope_notes=parsed.get("doc_b_scope"),
                ),
                resolution_notes=parsed.get("resolution_notes", default_res_notes),
                confidence=parsed.get("confidence", "medium") if parsed.get("confidence") in ("high", "medium", "low") else "medium",
            )

        except Exception as exc:
            # Fallback heuristic comparison if LLM JSON decode fails
            if is_ar_topic:
                fb_summary = f"تمت مقارنة موضوع '{topic}' بين الوثيقتين ({filename_a}) و ({filename_b})."
                fb_res = "يوصى بالرجوع إلى الوثائق الأصلية للتحقق من الأحكام والاشتراطات قبل اعتماد الإجراء."
            else:
                fb_summary = f"Compared '{topic}' across {filename_a} and {filename_b}."
                fb_res = "Automatic fallback analysis executed."

            return CompareResponse(
                topic=topic,
                relationship=ComparisonRelationship.AGREEMENT if chunks_a[0].text == chunks_b[0].text else ComparisonRelationship.POSSIBLE_CONFLICT,
                summary=fb_summary,
                document_a=DocumentClaim(
                    document_id=document_a_id,
                    filename=filename_a,
                    claim=chunks_a[0].text[:200],
                    evidence=evidence_a,
                ),
                document_b=DocumentClaim(
                    document_id=document_b_id_val,
                    filename=filename_b,
                    claim=chunks_b[0].text[:200],
                    evidence=evidence_b,
                ),
                resolution_notes=fb_res,
                confidence="low",
            )
