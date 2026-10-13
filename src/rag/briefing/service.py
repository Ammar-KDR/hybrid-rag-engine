import json
import re
import urllib.request
from typing import Optional

from rag.api.schemas.ask import EvidenceRef
from rag.api.schemas.brief import (
    BriefFinding,
    BriefResponse,
)
from rag.config import settings
from rag.ingestion.registry import DocumentRegistry
from rag.pipeline import RAGPipeline
from rag.retrieval.model import RetrievalFilter
from rag.nlp.arabic import is_arabic_text


class MultiDocumentBriefingService:
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

    def generate_briefing(
        self,
        document_ids: list[str],
        focus: str = "Executive Summary, Critical Policies, and Key Dates",
        max_findings: int = 8,
    ) -> BriefResponse:
        analyzed_filenames = []
        doc_evidence_map = {}
        all_evidence = []
        global_ref_counter = 1

        for doc_id in document_ids:
            rec = self.registry.get(doc_id) or {}
            filename = rec.get("filename", f"Doc {doc_id[:8]}")
            analyzed_filenames.append(filename)

            # Scoped retrieval for this document
            filt = RetrievalFilter(document_ids=(doc_id,))
            candidates = self.pipeline.retriever.retrieve(query=focus, top_k=4, filter=filt)
            reranked = (
                self.pipeline.reranker.rerank(query=focus, candidates=candidates)[:3]
                if candidates
                else []
            )

            doc_evidence_list = []
            for chunk in reranked:
                ev = self._build_evidence_ref(chunk, global_ref_counter, doc_id, filename)
                doc_evidence_list.append(ev)
                all_evidence.append(ev)
                global_ref_counter += 1

            doc_evidence_map[doc_id] = doc_evidence_list

        is_ar_focus = is_arabic_text(focus) or any(is_arabic_text(f) for f in analyzed_filenames)

        if not all_evidence:
            empty_summary = (
                "لم يتم العثور على مقاطع أو أدلة وثيقة الصلة بمحور التركيز المطلوب عبر الوثائق المحددة."
                if is_ar_focus
                else "No relevant evidence passages found for the requested focus across the selected documents."
            )
            return BriefResponse(
                focus=focus,
                document_count=len(document_ids),
                executive_summary=empty_summary,
                findings=[],
                analyzed_documents=analyzed_filenames,
            )

        # Build prompt evidence text
        evidence_blocks = []
        for ev in all_evidence:
            evidence_blocks.append(
                f"[Ref #{ev.reference} | {ev.filename}]\n{ev.text}"
            )
        evidence_str = "\n\n".join(evidence_blocks)

        system_prompt = (
            "You are an executive intelligence briefing analyst.\n"
            "Synthesize the provided document evidence into an executive briefing for senior leadership.\n\n"
            "RULES:\n"
            "1. Ground all findings strictly in the provided text.\n"
            "2. Identify the most critical policies, technical standards, compliance mandates, or action items.\n"
            "3. Assign each finding a category: 'policy', 'technical', 'compliance', or 'action_item'.\n"
            "4. Specify the reference number (e.g. 1, 2) of the primary evidence chunk supporting each finding.\n"
            "5. Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "executive_summary": "Comprehensive 2-4 sentence executive overview of the corpus",\n'
            '  "findings": [\n'
            '    {\n'
            '      "title": "Concise headline",\n'
            '      "description": "Clear explanation of the rule, mandate, or finding",\n'
            '      "category": "policy" | "technical" | "compliance" | "action_item",\n'
            '      "primary_ref": 1\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        if is_ar_focus:
            system_prompt += (
                "\n\nCRITICAL LANGUAGE INSTRUCTION:\n"
                "The focus and documents are in Arabic. You MUST generate all text content in the JSON "
                "('executive_summary', 'title', 'description') in formal, authoritative Arabic (لغة عربية فصحى رسمية). "
                "The JSON keys and 'category' enum values must remain in standard English."
            )

        user_content = (
            f"Focus: {focus}\n"
            f"Target Document Count: {len(document_ids)}\n\n"
            f"EVIDENCE PASSAGES:\n{evidence_str}\n\n"
            "JSON Briefing:"
        )

        try:
            clean_url = self.base_url.rstrip("/")
            if clean_url.endswith("/v1"):
                clean_url = clean_url[:-3]

            raw_json = ""
            # Try native Ollama /api/chat first with think=False via urllib.request
            try:
                native_payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "think": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 1024,
                    },
                    "keep_alive": -1,
                    "stream": False,
                }
                req_native = urllib.request.Request(
                    f"{clean_url}/api/chat",
                    data=json.dumps(native_payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "ExecutiveBriefing"},
                )
                with urllib.request.urlopen(req_native, timeout=45.0) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    if "message" in resp_data:
                        raw_json = resp_data["message"].get("content", "").strip()
                    elif "choices" in resp_data:
                        raw_json = resp_data["choices"][0]["message"].get("content", "").strip()
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
                    "max_tokens": 1024,
                }
                req = urllib.request.Request(
                    chat_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "ExecutiveBriefing"},
                )
                with urllib.request.urlopen(req, timeout=30.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if "choices" in data:
                        raw_json = data["choices"][0]["message"]["content"].strip()
                    elif "message" in data:
                        raw_json = data["message"]["content"].strip()

            # Clean <think> tags if present
            raw_json = re.sub(r"<think>.*?</think>", "", raw_json, flags=re.DOTALL).strip()
            raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json, flags=re.MULTILINE)
            raw_json = re.sub(r"```$", "", raw_json, flags=re.MULTILINE).strip()

            parsed = json.loads(raw_json)

            default_exec = (
                f"تم تلخيص وتركيب الإيجاز التنفيذي حول '{focus}' استناداً إلى الوثائق المحددة."
                if is_ar_focus
                else "Executive briefing generated."
            )
            exec_summary = parsed.get("executive_summary", default_exec)
            raw_findings = parsed.get("findings", [])[:max_findings]

            ref_to_ev = {ev.reference: ev for ev in all_evidence}
            findings = []

            for f in raw_findings:
                cat = str(f.get("category", "policy")).lower()
                if cat not in ("policy", "technical", "compliance", "action_item"):
                    cat = "policy"

                primary_ref = f.get("primary_ref")
                ev_list = []
                if primary_ref in ref_to_ev:
                    ev_list.append(ref_to_ev[primary_ref])
                elif all_evidence:
                    ev_list.append(all_evidence[0])

                findings.append(
                    BriefFinding(
                        title=f.get("title", "نتيجة رئيسية" if is_ar_focus else "Key Finding"),
                        description=f.get("description", ""),
                        category=cat,
                        evidence=ev_list,
                    )
                )

            return BriefResponse(
                focus=focus,
                document_count=len(document_ids),
                executive_summary=exec_summary,
                findings=findings,
                analyzed_documents=analyzed_filenames,
            )

        except Exception:
            # Fallback heuristic synthesis
            fallback_findings = []
            for ev in all_evidence[:max_findings]:
                fallback_findings.append(
                    BriefFinding(
                        title=f"مستخلص من {ev.filename}" if is_ar_focus else f"Finding from {ev.filename}",
                        description=ev.text[:250] + ("..." if len(ev.text) > 250 else ""),
                        category="policy",
                        evidence=[ev],
                    )
                )

            fb_summary = (
                f"تم تركيب وتحليل {len(document_ids)} وثائق بالتركيز على محور '{focus}'."
                if is_ar_focus
                else f"Synthesized analysis of {len(document_ids)} documents focusing on '{focus}'."
            )

            return BriefResponse(
                focus=focus,
                document_count=len(document_ids),
                executive_summary=fb_summary,
                findings=fallback_findings,
                analyzed_documents=analyzed_filenames,
            )
