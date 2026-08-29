import os
import time
from dataclasses import dataclass

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