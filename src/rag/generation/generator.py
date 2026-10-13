import os
import time
from dataclasses import dataclass
from openai import OpenAI

from google import genai
from google.genai import types

from .prompt import GenerationPrompt
from .model import GenerationResult
from rag.config import settings




class GeminiGenerationService:

    def __init__(
        self,
        model: str = "gemini-3.7-flash",
    ):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set"
            )

        self.model = model
        self.client = genai.Client(
            api_key=api_key
        )

    def generate(
        self,
        prompt: GenerationPrompt,
    ) -> GenerationResult:

        start = time.perf_counter()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt.user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=prompt.system_prompt,

                thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                ),

                temperature=0.2,
                max_output_tokens=1024,
            ),
        )

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        usage = response.usage_metadata

        return GenerationResult(
            text=response.text or "",
            model=self.model,

            input_tokens=(
                usage.prompt_token_count
                if usage
                else None
            ),

            output_tokens=(
                usage.candidates_token_count
                if usage
                else None
            ),

            total_tokens=(
                usage.total_token_count
                if usage
                else None
            ),

            latency_ms=latency_ms,
        )




class LMStudioGenerationService:

    def __init__(
        self,
        model: str = settings.LM_STUDIO_MODEL,
        base_url: str = settings.LM_STUDIO_BASE_URL,
    ):
        self.model = model

        self.client = OpenAI(
            base_url=base_url,
            api_key="lm-studio",
        )


    def generate(
        self,
        prompt: GenerationPrompt,
    ) -> GenerationResult:

        start = time.perf_counter()

        response = self.client.chat.completions.create(
            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": prompt.system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt.user_prompt,
                },
            ],

            temperature=0.2,
            max_tokens=1024,
        )

        latency_ms = (
            time.perf_counter() - start
        ) * 1000


        # --------------------------------------------------
        # Extract generated text
        # --------------------------------------------------

        text = (
            response.choices[0].message.content
            or ""
        )


        # --------------------------------------------------
        # Token usage
        # --------------------------------------------------

        usage = response.usage

        return GenerationResult(
            text=text,
            model=self.model,

            input_tokens=(
                usage.prompt_tokens
                if usage
                else None
            ),

            output_tokens=(
                usage.completion_tokens
                if usage
                else None
            ),

            total_tokens=(
                usage.total_tokens
                if usage
                else None
            ),

            latency_ms=latency_ms,
        )


class OllamaGenerationService:

    def __init__(
        self,
        model: str = settings.OLLAMA_MODEL,
        base_url: str = settings.OLLAMA_BASE_URL,
    ):
        self.model = model
        clean_url = base_url.rstrip("/")
        if clean_url.endswith("/v1"):
            clean_url = clean_url[:-3]
        self.native_url = clean_url
        self.client = OpenAI(
            base_url=base_url,
            api_key="ollama",
        )

    def generate(
        self,
        prompt: GenerationPrompt,
    ) -> GenerationResult:

        start = time.perf_counter()

        # Try native Ollama /api/chat first with think=False for ultra-fast GPU generation
        try:
            import requests

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": prompt.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt.user_prompt,
                    },
                ],
                "think": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 1024,
                },
                "keep_alive": -1,
                "stream": False,
            }
            resp = requests.post(
                f"{self.native_url}/api/chat",
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            latency_ms = (
                time.perf_counter() - start
            ) * 1000

            text = data.get("message", {}).get("content", "")
            prompt_tokens = data.get("prompt_eval_count")
            completion_tokens = data.get("eval_count")
            total_tokens = (
                prompt_tokens + completion_tokens
                if prompt_tokens is not None and completion_tokens is not None
                else None
            )

            return GenerationResult(
                text=text,
                model=self.model,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
            )
        except Exception:
            # Fallback to OpenAI API client if native call fails
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt.user_prompt,
                    },
                ],
                temperature=0.2,
                max_tokens=1024,
                extra_body={"keep_alive": -1},
            )

            latency_ms = (
                time.perf_counter() - start
            ) * 1000

            msg = response.choices[0].message
            text = (
                msg.content
                or getattr(msg, "reasoning", "")
                or getattr(msg, "reasoning_content", "")
                or ""
            )

            usage = response.usage

            return GenerationResult(
                text=text,
                model=self.model,
                input_tokens=(
                    usage.prompt_tokens
                    if usage
                    else None
                ),
                output_tokens=(
                    usage.completion_tokens
                    if usage
                    else None
                ),
                total_tokens=(
                    usage.total_tokens
                    if usage
                    else None
                ),
                latency_ms=latency_ms,
            )