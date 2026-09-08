from rag.verification.model import (
    Claim,
    ClaimFaithfulness,
    SupportVerdict,
)

from rag.verification.faithfulness import (
    FaithfulnessEvaluator,
)


class FakeFaithfulnessVerifier:

    VERDICTS = {
        "Supported claim": SupportVerdict.SUPPORTED,
        "Supported claim A": SupportVerdict.SUPPORTED,
        "Supported claim B": SupportVerdict.SUPPORTED,
        "Partial claim": SupportVerdict.PARTIALLY_SUPPORTED,
        "Unsupported claim": SupportVerdict.UNSUPPORTED,
        "Unsupported factual statement": SupportVerdict.UNSUPPORTED,
        "Contradicted claim": SupportVerdict.CONTRADICTED,
    }

    def verify(
        self,
        claim: Claim,
        evidence_text: str,
    ) -> ClaimFaithfulness:

        verdict = self.VERDICTS.get(
            claim.text,
            SupportVerdict.UNSUPPORTED,
        )

        return ClaimFaithfulness(
            claim_text=claim.text,
            verdict=verdict,
            explanation="Fake deterministic faithfulness result.",
        )


def test_all_supported_claims():

    claims = [
        Claim(
            text="Supported claim A",
            citations=[1],
        ),
        Claim(
            text="Supported claim B",
            citations=[2],
        ),
    ]

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=claims,
        evidence_text="Fake evidence",
    )

    assert result.total_claims == 2
    assert result.supported_claims == 2

    assert result.partially_supported_claims == 0
    assert result.unsupported_claims == 0
    assert result.contradicted_claims == 0

    assert len(result.claim_results) == 2


def test_mixed_faithfulness_results():

    claims = [
        Claim(
            text="Supported claim",
            citations=[1],
        ),
        Claim(
            text="Partial claim",
            citations=[2],
        ),
        Claim(
            text="Unsupported factual statement",
            citations=[3],
        ),
        Claim(
            text="Contradicted claim",
            citations=[4],
        ),
    ]

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=claims,
        evidence_text="Fake evidence",
    )

    assert result.total_claims == 4

    assert result.supported_claims == 1
    assert result.partially_supported_claims == 1
    assert result.unsupported_claims == 1
    assert result.contradicted_claims == 1


def test_uncited_claim_can_still_be_faithful():

    claims = [
        Claim(
            text="Supported claim",
            citations=[],
        ),
    ]

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=claims,
        evidence_text="Evidence supports the claim.",
    )

    assert result.total_claims == 1
    assert result.supported_claims == 1

    assert (
        result.claim_results[0].verdict
        == SupportVerdict.SUPPORTED
    )


def test_empty_claim_list():

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=[],
        evidence_text="Some evidence.",
    )

    assert result.total_claims == 0

    assert result.supported_claims == 0
    assert result.partially_supported_claims == 0
    assert result.unsupported_claims == 0
    assert result.contradicted_claims == 0

    assert result.claim_results == []


def test_preserves_individual_claim_results():

    claims = [
        Claim(
            text="Supported claim",
            citations=[1],
        ),
        Claim(
            text="Unsupported claim",
            citations=[2],
        ),
    ]

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=claims,
        evidence_text="Fake evidence",
    )

    assert len(result.claim_results) == 2

    assert (
        result.claim_results[0].claim_text
        == "Supported claim"
    )

    assert (
        result.claim_results[0].verdict
        == SupportVerdict.SUPPORTED
    )

    assert (
        result.claim_results[1].claim_text
        == "Unsupported claim"
    )

    assert (
        result.claim_results[1].verdict
        == SupportVerdict.UNSUPPORTED
    )


def test_partial_claim_is_preserved():

    claims = [
        Claim(
            text="Partial claim",
            citations=[1],
        ),
    ]

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=claims,
        evidence_text="Fake evidence",
    )

    assert result.total_claims == 1
    assert result.supported_claims == 0
    assert result.partially_supported_claims == 1
    assert result.unsupported_claims == 0
    assert result.contradicted_claims == 0

    assert (
        result.claim_results[0].verdict
        == SupportVerdict.PARTIALLY_SUPPORTED
    )


def test_contradicted_claim_is_preserved():

    claims = [
        Claim(
            text="Contradicted claim",
            citations=[1],
        ),
    ]

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=claims,
        evidence_text="Fake evidence",
    )

    assert result.total_claims == 1
    assert result.supported_claims == 0
    assert result.partially_supported_claims == 0
    assert result.unsupported_claims == 0
    assert result.contradicted_claims == 1

    assert (
        result.claim_results[0].verdict
        == SupportVerdict.CONTRADICTED
    )


def test_unknown_claim_defaults_to_unsupported():

    claims = [
        Claim(
            text="Completely unknown claim",
            citations=[1],
        ),
    ]

    evaluator = FaithfulnessEvaluator(
        verifier=FakeFaithfulnessVerifier()
    )

    result = evaluator.evaluate(
        claims=claims,
        evidence_text="Fake evidence",
    )

    assert result.total_claims == 1
    assert result.supported_claims == 0
    assert result.partially_supported_claims == 0
    assert result.unsupported_claims == 1
    assert result.contradicted_claims == 0

    assert (
        result.claim_results[0].verdict
        == SupportVerdict.UNSUPPORTED
    )