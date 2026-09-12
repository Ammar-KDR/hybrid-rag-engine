from dataclasses import dataclass
from enum import Enum
from typing import Literal
import re
from openai import OpenAI
from pydantic import BaseModel
from rag.config import settings


class CorrectnessVerdict(str, Enum):
    CORRECT = "CORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"


@dataclass(frozen=True)
class ClaimCorrectnessResult:
    claim: str
    verdict: CorrectnessVerdict
    explanation: str


@dataclass(frozen=True)
class GoldenCorrectnessEvaluation:
    total_claims: int
    correct_claims: int
    partially_correct_claims: int
    incorrect_claims: int
    correctness_score: float | None
    claim_results: list[ClaimCorrectnessResult]

class GoldenCorrectnessEvaluator:

    def __init__(
        self,
        judge,
    ):
        self.judge = judge


    def evaluate(
        self,
        case,
        claims,
    ) -> GoldenCorrectnessEvaluation:

        # Unanswerable cases are evaluated through
        # abstention behavior, not correctness.
        if not case.answerable:
            return GoldenCorrectnessEvaluation(
                total_claims=0,
                correct_claims=0,
                partially_correct_claims=0,
                incorrect_claims=0,
                correctness_score=None,
                claim_results=[],
            )

        factual_claims = [
            claim
            for claim in claims
            if claim.text.strip()
        ]

        if not factual_claims:
            return GoldenCorrectnessEvaluation(
                total_claims=0,
                correct_claims=0,
                partially_correct_claims=0,
                incorrect_claims=0,
                correctness_score=None,
                claim_results=[],
            )

        results = []

        for claim in factual_claims:

            result = self.judge.evaluate(
               
                claim=claim.text,
                
                evidence_spans=[
                    span.text
                    for span in case.evidence_spans
                ],
            )

            results.append(result)

        correct = sum(
            result.verdict
            == CorrectnessVerdict.CORRECT
            for result in results
        )

        partial = sum(
            result.verdict
            == CorrectnessVerdict.PARTIALLY_CORRECT
            for result in results
        )

        incorrect = sum(
            result.verdict
            == CorrectnessVerdict.INCORRECT
            for result in results
        )

        score = (
            correct
            +
            (0.5 * partial)
        ) / len(results)

        return GoldenCorrectnessEvaluation(
            total_claims=len(results),
            correct_claims=correct,
            partially_correct_claims=partial,
            incorrect_claims=incorrect,
            correctness_score=score,
            claim_results=results,
        )
CORRECTNESS_SYSTEM_PROMPT = """
You are a claim correctness evaluator for a RAG benchmark.

You will receive:

- one generated factual claim
- authoritative GOLD evidence

Your ONLY task is to determine whether the factual content present
inside the claim is correct according to the gold evidence.

Do not use outside knowledge.
Do not evaluate completeness.
Do not evaluate whether the claim answers the whole question.
Do not penalize a claim for omitting other facts.
Do not require a claim to mention every fact in the gold evidence.

Judge ONLY what the claim actually says.

Use exactly one verdict:

CORRECT:
Every factual assertion made by the claim is supported by or directly
consistent with the gold evidence.

PARTIALLY_CORRECT:
The claim itself contains multiple factual assertions, and at least
one is supported while at least one other assertion is unsupported
or conflicts with the gold evidence.

INCORRECT:
The claim's factual assertion is unsupported by or conflicts with the
gold evidence.

CRITICAL RULE:

Missing information is NEVER a correctness error.

Example:

Gold evidence:
Use free -h to inspect system memory.
Use ps aux --sort=-%mem to inspect process memory.

Claim:
Use free -h to inspect system memory.

Verdict:
CORRECT

The claim does not need to mention ps aux. That is a completeness issue,
not a correctness issue.

Example:

Gold evidence:
HTTP 429 means the request rate was exceeded.

Claim:
HTTP 429 means the request rate was exceeded and DNS resolution failed.

Verdict:
PARTIALLY_CORRECT

Example:

Gold evidence:
HTTP 429 means the request rate was exceeded.

Claim:
HTTP 429 means authentication failed.

Verdict:
INCORRECT

Return a very short explanation.
Maximum 1 sentence.
"""

class _CorrectnessSchema(BaseModel):

    verdict: Literal[
        "CORRECT",
        "PARTIALLY_CORRECT",
        "INCORRECT",
    ]

    explanation: str

class LMStudioCorrectnessJudge:

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


    def evaluate(
    self,
    claim: str,
    evidence_spans: list[str],
) -> ClaimCorrectnessResult:

        evidence_text = "\n\n".join(
            f"[Gold Evidence {index}]\n{evidence}"
            for index, evidence
            in enumerate(
                evidence_spans,
                start=1,
            )
        )

        last_exception = None

        for attempt in range(3):

            response = self.client.chat.completions.create(
                model=self.model,

                messages=[
                    {
                        "role": "system",
                        "content": CORRECTNESS_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": (
                            "<claim>\n"
                            f"{claim}\n"
                            "</claim>\n\n"

                            "<gold_evidence>\n"
                            f"{evidence_text}\n"
                            "</gold_evidence>"
                        ),
                    },
                ],

                temperature=0.0,
                max_tokens=512,

                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "golden_correctness",
                        "schema": (
                            _CorrectnessSchema
                            .model_json_schema()
                        ),
                    },
                },
            )

            response_text = (
                response.choices[0].message.content
                or ""
            )

            # ------------------------------------------
            # First try: valid structured JSON
            # ------------------------------------------

            try:

                parsed = (
                    _CorrectnessSchema
                    .model_validate_json(
                        response_text
                    )
                )

                return ClaimCorrectnessResult(
                    claim=claim,
                    verdict=CorrectnessVerdict(
                        parsed.verdict
                    ),
                    explanation=(
                        parsed.explanation.strip()
                    ),
                )

            except Exception as exc:

                last_exception = exc


            # ------------------------------------------
            # Second try:
            # recover verdict from truncated JSON
            # ------------------------------------------

            verdict_match = re.search(
                r'"verdict"\s*:\s*"'
                r'(CORRECT|PARTIALLY_CORRECT|INCORRECT)'
                r'"',
                response_text,
            )

            if verdict_match is not None:

                return ClaimCorrectnessResult(
                    claim=claim,
                    verdict=CorrectnessVerdict(
                        verdict_match.group(1)
                    ),
                    explanation=(
                        "Verdict recovered from truncated "
                        "structured output."
                    ),
                )


            # ------------------------------------------
            # Otherwise retry
            # ------------------------------------------

            print(
                f"Correctness judge attempt "
                f"{attempt + 1} failed."
            )

            print(
                "Raw response:",
                response_text,
            )


        # ----------------------------------------------
        # All 3 attempts failed
        # ----------------------------------------------

        raise RuntimeError(
            "Correctness judge returned invalid JSON "
            "after 3 attempts."
        ) from last_exception