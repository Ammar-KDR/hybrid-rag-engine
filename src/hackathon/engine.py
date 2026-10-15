"""Hackathon Generation Engine using local Ollama and Exact Context Matching."""

import json
import re
import urllib.request
from typing import Any, Dict, List, Optional

from src.hackathon.corpus import HackathonCorpus
from src.hackathon.router import IntentRouter, RouteDecision


OUT_OF_SCOPE_REFUSAL = (
    "عذراً، لا تتوفر لدي معلومات عن هذا الموضوع. "
    "أستطيع المساعدة في خدمات جواز السفر ودفتر العائلة والبطاقة الذكية فقط."
)


class HackathonEngine:
    """End-to-end question answering engine adhering to the hackathon benchmark."""

    def __init__(
        self,
        corpus: Optional[HackathonCorpus] = None,
        router: Optional[IntentRouter] = None,
        model_name: str = "command-r7b-arabic:7b",
        base_url: str = "http://127.0.0.1:11434",
    ):
        self.corpus = corpus or HackathonCorpus()
        self.router = router or IntentRouter(self.corpus)
        self.base_url = base_url.rstrip("/")
        self.model_name = self._resolve_model_name(model_name, self.base_url)

    def _resolve_model_name(self, requested_name: str, base_url: str) -> str:
        try:
            req = urllib.request.Request(f"{base_url}/api/tags")
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                if requested_name in models:
                    return requested_name
                prefix = requested_name.split(":")[0]
                for m in models:
                    if m.startswith(prefix):
                        return m
                for candidate in ["qwen2.5:3b", "qwen3.5:4b"]:
                    if candidate in models:
                        return candidate
                if models:
                    return models[0]
        except Exception:
            pass
        return requested_name

    def answer_question(
        self,
        question: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Answers a single question returning the exact dict structure."""
        decision = self.router.route(question, history=history)

        if decision.is_out_of_scope or not decision.targets:
            return {
                "answer": OUT_OF_SCOPE_REFUSAL,
                "contexts": [],
            }

        # Collect target contexts
        contexts: List[str] = []
        for target in decision.targets:
            doc = self.corpus.get_service(target.doc_type, target.situation)
            if not doc:
                continue

            for sec_key in target.section_keys:
                if sec_key in doc.sections:
                    sec = doc.sections[sec_key]
                    if sec.context_string and sec.context_string not in contexts:
                        contexts.append(sec.context_string)

        if not contexts:
            return {
                "answer": OUT_OF_SCOPE_REFUSAL,
                "contexts": [],
            }

        # Generate answer using Ollama
        context_block = "\n".join(contexts)
        prompt = (
            "أنت مساعد حكومي رسمي لدائرة الأحوال المدنية والجوازات الأردنية.\n"
            "أجب عن سؤال المواطن بلغة عربية دقيقة، موجزة، ومباشرة بناءً على السياق الرسمي المرفق فقط.\n"
            "إرشادات هامة:\n"
            "- التزم حصرياً بالمعلومات الموجودة في السياق، ولا تضف شروطاً أو متطلبات من عندك لم ترد في السياق.\n"
            "- إذا كان السؤال استفساراً عن إمكانية (مثل: بقدر، هل يجوز، ممكن)، أجب بنعم يمكنك أو لا ثم اذكر المكان أو التفصيل المذكور في السياق فقط.\n"
            "- إذا كان السؤال عن معلومة محددة (مثل عدد الصور، أو الرسوم، أو المدة الزمنية)، اذكر تلك المعلومة المحددة فقط دون سرد باقي الوثائق أو الشروط غير المطلوبة.\n"
            "- إذا كان السؤال يقارن بين خدمتين، أجب بإيجاز عن كلتا الخدمتين.\n\n"
            f"السياق الرسمي:\n{context_block}\n\n"
            f"سؤال المواطن: {question}\n\n"
            "الجواب المباشر:"
        )

        try:
            raw_answer = self._call_ollama(prompt)
            clean_answer = self._clean_llm_response(raw_answer)
        except Exception:
            # Fallback if Ollama has a momentary timeout
            clean_answer = self._generate_heuristic_fallback(decision, question, contexts)

        return {
            "answer": clean_answer,
            "contexts": contexts,
        }

    def _call_ollama(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.05,
                "top_p": 0.85,
                "num_ctx": 4096,
                "num_predict": 250,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")

    def _clean_llm_response(self, text: str) -> str:
        # Strip <think>...</think> if present (Qwen 3.5 reasoning format)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Strip leading phrases like "الإجابة:" or "الجواب:"
        text = re.sub(r"^(?:الإجابة|الجواب|الرد)\s*[:\-]\s*", "", text.strip())
        return text.strip()

    def _generate_heuristic_fallback(
        self,
        decision: RouteDecision,
        question: str,
        contexts: List[str],
    ) -> str:
        # If LLM is unreachable, extract the content directly from the context string
        if contexts:
            first_ctx = contexts[0]
            if ":" in first_ctx:
                return first_ctx.split(":", 1)[1].strip()
            return first_ctx
        return OUT_OF_SCOPE_REFUSAL
