import os
import time
from dataclasses import dataclass
from openai import OpenAI

from google import genai
from google.genai import types

from .prompt import GenerationPrompt
from .model import GenerationResult





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
        model: str = "qwen/qwen3-4b-2507",
        base_url: str = "http://127.0.0.1:1234/v1",
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