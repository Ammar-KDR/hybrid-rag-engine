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

UNCLEAR_CLARIFICATION = (
    "يرجى تحديد نوع المعاملة التي ترغب بها "
    "(جواز السفر، أو دفتر العائلة، أو البطاقة الذكية) لنتمكن من تزويدك بالشروط والرسوم والوثائق بدقة."
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

        if decision.is_unclear:
            return {
                "answer": UNCLEAR_CLARIFICATION,
                "contexts": [],
            }

        if decision.is_out_of_scope or not decision.targets:
            return {
                "answer": OUT_OF_SCOPE_REFUSAL,
                "contexts": [],
            }

        # Collect target contexts strictly from routed services
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

        # Generate answer using local Ollama model
        context_block = "\n\n".join(contexts)
        prompt = (
            "أنت مساعد حكومي رسمي لدائرة الأحوال المدنية والجوازات الأردنية.\n"
            "مهمتك: الإجابة عن سؤال المواطن بدقة وأمانة بناءً على النصوص الرسمية المرفقة فقط.\n\n"
            "القواعد الصارمة للإجابة:\n"
            "1. طبق حصرياً شروط وأحكام الخدمة المعنية المسترجعة، ولا تخلط إطلاقاً بين خدمات مختلفة أو تنقل شرطاً من معاملة لأخرى.\n"
            "2. لا تذكر أي مبلغ مالي أو غرامة أو كفالة أو مدة إنجاز إلا إذا كانت واردة ومسندة بنص صريح في السياق المرفق.\n"
            "3. إذا كان السؤال عن الرسوم، طابق بدقة تفاصيل المواطن (مثل: العمر، الصفة مدني/عسكري، مكان التواجد، ومدة الصلاحية) مع البند المالي المناسب في السياق: لا تطبق بنود العسكريين لمواطن مدني، بل اختر بند المواطن المدني المطابق لعمره وصلاحية جوازه (فإذا كان فوق 16 سنة وباقٍ على جوازه أقل من 180 يوماً / 6 أشهر فإن الرسم المقرر في النص هو 50 ديناراً وليس 20 ديناراً).\n"
            "4. في معاملات بدل الفاقد، اذكر دائماً الرسم الأساسي بالإضافة إلى قيمة استيفاء التعهد أو الكفالة المقررة.\n"
            "5. لا تخترع ولا تخمن أي مدد انتظار أو إجراءات غير موجودة في السياق. وإذا كانت معلومة معينة غير مذكورة في الوثائق المرفقة (مثل عدم وجود مدة انتظار محددة)، اذكر بصراحة أنها غير مذكورة في النصوص الرسمية.\n"
            "6. إذا كانت الرسوم أو الشروط تعتمد على معلومات ناقصة لم يذكرها المواطن، اسأل المواطن عنها أو اذكر الخيارات المقررة بدلاً من افتراض تفاصيل غير مؤكدة.\n"
            "7. إذا تضمن السؤال عدة معاملات أو استفسارات منفصلة، أجب عن كل منها في بند مرقم ومستقل بدقة واكتمال مع تجاهل التفاصيل الجانبية غير الإجرائية.\n\n"
            f"السياق الرسمي المعتمد:\n{context_block}\n\n"
            f"سؤال المواطن: {question}\n\n"
            "الجواب المباشر:"
        )

        try:
            raw_answer = self._call_ollama(prompt)
            clean_answer = self._clean_llm_response(raw_answer)
        except Exception:
            clean_answer = self._generate_fallback(decision, question, contexts)

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
                "num_predict": 512,
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
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"^(?:الإجابة|الجواب|الرد)\s*[:\-]\s*", "", text.strip())
        return text.strip()

    def _generate_fallback(
        self,
        decision: RouteDecision,
        question: str,
        contexts: List[str],
    ) -> str:
        if contexts:
            first_ctx = contexts[0]
            if ":" in first_ctx:
                return first_ctx.split(":", 1)[1].strip()
            return first_ctx
        return OUT_OF_SCOPE_REFUSAL
