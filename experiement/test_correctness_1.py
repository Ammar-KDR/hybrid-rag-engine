from types import SimpleNamespace

import pytest

from rag.evaluation.gold_correctness_eval import (
    ClaimCorrectnessResult,
    CorrectnessVerdict,
    GoldenCorrectnessEvaluator,
)


class FakeCorrectnessJudge:

    def __init__(
        self,
        verdicts: dict[str, CorrectnessVerdict],
    ):
        self.verdicts = verdicts

    def evaluate(
        self,
        question,
        claim,
        reference_answer,
        required_facts,
        evidence_spans,
    ):

        verdict = self.verdicts[claim]

        return ClaimCorrectnessResult(
            claim=claim,
            verdict=verdict,
            explanation="Fake test explanation.",
        )


def make_case(
    answerable: bool = True,
):

    return SimpleNamespace(
        question="Test question?",
        answerable=answerable,
        reference_answer="Reference answer.",
        required_facts=[
            SimpleNamespace(
                description="Required fact A",
                required=True,
            ),
            SimpleNamespace(
                description="Optional fact",
                required=False,
            ),
        ],
        evidence_spans=[
            SimpleNamespace(
                text="Gold evidence."
            )
        ],
    )


def make_claims(
    *texts: str,
):

    return [
        SimpleNamespace(
            text=text
        )
        for text in texts
    ]


def test_all_claims_correct():

    judge = FakeCorrectnessJudge(
        {
            "Claim A": CorrectnessVerdict.CORRECT,
            "Claim B": CorrectnessVerdict.CORRECT,
        }
    )

    evaluator = GoldenCorrectnessEvaluator(
        judge=judge
    )

    result = evaluator.evaluate(
        case=make_case(),
        claims=make_claims(
            "Claim A",
            "Claim B",
        ),
    )

    assert result.total_claims == 2
    assert result.correct_claims == 2
    assert result.partially_correct_claims == 0
    assert result.incorrect_claims == 0
    assert result.correctness_score == 1.0


def test_correct_and_incorrect_claims():

    judge = FakeCorrectnessJudge(
        {
            "Claim A": CorrectnessVerdict.CORRECT,
            "Claim B": CorrectnessVerdict.INCORRECT,
        }
    )

    evaluator = GoldenCorrectnessEvaluator(
        judge=judge
    )

    result = evaluator.evaluate(
        case=make_case(),
        claims=make_claims(
            "Claim A",
            "Claim B",
        ),
    )

    assert result.total_claims == 2
    assert result.correct_claims == 1
    assert result.partially_correct_claims == 0
    assert result.incorrect_claims == 1

    assert result.correctness_score == pytest.approx(
        0.5
    )


def test_correct_and_partially_correct_claims():

    judge = FakeCorrectnessJudge(
        {
            "Claim A": CorrectnessVerdict.CORRECT,
            "Claim B": CorrectnessVerdict.PARTIALLY_CORRECT,
        }
    )

    evaluator = GoldenCorrectnessEvaluator(
        judge=judge
    )

    result = evaluator.evaluate(
        case=make_case(),
        claims=make_claims(
            "Claim A",
            "Claim B",
        ),
    )

    assert result.total_claims == 2
    assert result.correct_claims == 1
    assert result.partially_correct_claims == 1
    assert result.incorrect_claims == 0

    assert result.correctness_score == pytest.approx(
        0.75
    )


def test_unanswerable_case_returns_none():

    judge = FakeCorrectnessJudge(
        {}
    )

    evaluator = GoldenCorrectnessEvaluator(
        judge=judge
    )

    result = evaluator.evaluate(
        case=make_case(
            answerable=False
        ),
        claims=make_claims(
            "Some claim"
        ),
    )

    assert result.total_claims == 0
    assert result.correct_claims == 0
    assert result.partially_correct_claims == 0
    assert result.incorrect_claims == 0
    assert result.correctness_score is None
    assert result.claim_results == []