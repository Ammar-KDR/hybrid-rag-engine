import json
import re
import urllib.request
from typing import Sequence

from rag.api.schemas.ask import ChatMessage
from rag.config import settings


PRONOUN_PATTERN = re.compile(
    r"\b(it|its|they|them|their|theirs|this|that|these|those)\b",
    re.IGNORECASE,
)

ELLIPTICAL_PATTERNS = [
    r"\bwhat about\b",
    r"\bhow about\b",
    r"\band what if\b",
    r"\bare there exceptions\b",
    r"\bdoes it\b",
    r"\bcan it\b",
    r"\bwhy is that\b",
    r"\bwho did that\b",
    r"\bany other\b",
    r"\bwhat else\b",
]


class QueryRewriter:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def should_rewrite(
        self,
        question: str,
        history: Sequence[ChatMessage],
    ) -> bool:
        if not history:
            return False

        q_lower = question.lower().strip()

        # Pronoun match
        if PRONOUN_PATTERN.search(q_lower):
            return True

        # Elliptical phrasing match
        for pat in ELLIPTICAL_PATTERNS:
            if re.search(pat, q_lower):
                return True

        # Short question (< 5 words) following a conversation
        words = q_lower.split()
        if len(words) < 5:
            return True

        return False

    def rewrite(
        self,
        question: str,
        history: Sequence[ChatMessage],
    ) -> tuple[str, bool]:
        if not self.should_rewrite(question, history):
            return question, False

        # Build conversation context from last 4 messages max
        recent_history = history[-4:]
        history_lines = []
        for msg in recent_history:
            role = "User" if msg.role == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.content}")

        history_text = "\n".join(history_lines)

        system_prompt = (
            "You are an expert search query reformulator.\n"
            "Given the recent conversation history and the user's latest follow-up question, "
            "rewrite the follow-up question into a single, self-contained standalone question "
            "suitable for document retrieval.\n\n"
            "RULES:\n"
            "1. Do NOT answer the question.\n"
            "2. Resolve all ambiguous pronouns ('it', 'they', 'that', 'this') to the specific subject mentioned previously.\n"
            "3. Output ONLY the standalone rewritten question with no explanation, preface, or quotation marks."
        )

        user_content = (
            f"Conversation History:\n{history_text}\n\n"
            f"Follow-up Question: {question}\n\n"
            "Standalone Question:"
        )

        try:
            # Prefer OpenAI-compatible /v1/chat/completions endpoint on Ollama
            chat_url = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.0,
                "max_tokens": 100,
            }

            req = urllib.request.Request(
                chat_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "QueryRewriter"},
            )

            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"].strip()

            # Clean quotes and unwanted prefixes
            cleaned = content.strip("\"' \n\r")
            if cleaned.lower().startswith("standalone question:"):
                cleaned = cleaned[20:].strip("\"' \n\r")

            if cleaned and len(cleaned) > 3:
                return cleaned, True

        except Exception:
            # Resilient fallback on any timeout or failure
            pass

        return question, False
