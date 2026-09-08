from rag.verification.model import (
    Claim,
    CitationVerification,
    CitationVerificationResult,
    SupportVerdict,
)
from rag.verification.runner import CitationVerificationRunner


class FakeVerifier:

    def verify(
        self,
        claim: Claim,
        reference: int,
        evidence_text: str,
    ) -> CitationVerification:

        if "configuration errors" in claim.text:
            verdict = SupportVerdict.SUPPORTED

        elif "kubectl logs" in claim.text:
            verdict = SupportVerdict.SUPPORTED

        elif "Pod ran out of memory" in claim.text:
            verdict = SupportVerdict.CONTRADICTED

        else:
            verdict = SupportVerdict.UNSUPPORTED

        return CitationVerification(
            claim_text=claim.text,
            reference=reference,
            verdict=verdict,
            explanation="Fake deterministic verification.",
        )


def test_runner_verifies_resolved_citations():

    runner = CitationVerificationRunner(
        verifier=FakeVerifier()
    )

    claims = [
        Claim(
            text="CrashLoopBackOff may be caused by configuration errors.",
            citations=[1],
        ),
        Claim(
            text="kubectl logs can inspect a failing container.",
            citations=[2],
        ),
    ]

    evidence_by_reference = {
        1: "Configuration errors can cause CrashLoopBackOff.",
        2: "Use kubectl logs to inspect container logs.",
    }

    result = runner.run(
        claims=claims,
        evidence_by_reference=evidence_by_reference,
    )

    assert len(result.verifications) == 2
    assert result.uncited_claims == []
    assert result.unresolved_references == []

    assert result.verifications[0].verdict == SupportVerdict.SUPPORTED
    assert result.verifications[0].reference == 1

    assert result.verifications[1].verdict == SupportVerdict.SUPPORTED
    assert result.verifications[1].reference == 2


def test_runner_tracks_uncited_claim():

    runner = CitationVerificationRunner(
        verifier=FakeVerifier()
    )

    claim = Claim(
        text="kubectl logs can inspect container output.",
        citations=[],
    )

    result = runner.run(
        claims=[claim],
        evidence_by_reference={},
    )

    assert result.verifications == []
    assert result.unresolved_references == []

    assert result.uncited_claims == [
        claim
    ]


def test_runner_tracks_unresolved_reference():

    runner = CitationVerificationRunner(
        verifier=FakeVerifier()
    )

    claim = Claim(
        text="This claim references missing evidence.",
        citations=[9],
    )

    result = runner.run(
        claims=[claim],
        evidence_by_reference={
            1: "Some existing evidence."
        },
    )

    assert result.verifications == []
    assert result.uncited_claims == []
    assert result.unresolved_references == [9]


def test_runner_deduplicates_unresolved_references():

    runner = CitationVerificationRunner(
        verifier=FakeVerifier()
    )

    claims = [
        Claim(
            text="First claim with missing evidence.",
            citations=[9],
        ),
        Claim(
            text="Second claim with the same missing evidence.",
            citations=[9],
        ),
    ]

    result = runner.run(
        claims=claims,
        evidence_by_reference={},
    )

    assert result.verifications == []
    assert result.uncited_claims == []

    assert result.unresolved_references == [9]


def test_runner_handles_supported_and_contradicted_claims():

    runner = CitationVerificationRunner(
        verifier=FakeVerifier()
    )

    claims = [
        Claim(
            text="CrashLoopBackOff may be caused by configuration errors.",
            citations=[1],
        ),
        Claim(
            text="HTTP 429 means the Pod ran out of memory.",
            citations=[2],
        ),
    ]

    evidence_by_reference = {
        1: "Configuration errors can cause CrashLoopBackOff.",
        2: "HTTP 429 means Too Many Requests.",
    }

    result = runner.run(
        claims=claims,
        evidence_by_reference=evidence_by_reference,
    )

    assert len(result.verifications) == 2

    assert (
        result.verifications[0].verdict
        == SupportVerdict.SUPPORTED
    )

    assert (
        result.verifications[1].verdict
        == SupportVerdict.CONTRADICTED
    )


def test_runner_handles_multiple_citations_for_one_claim():

    runner = CitationVerificationRunner(
        verifier=FakeVerifier()
    )

    claim = Claim(
        text="CrashLoopBackOff may be caused by configuration errors.",
        citations=[1, 2],
    )

    evidence_by_reference = {
        1: "Configuration errors can cause CrashLoopBackOff.",
        2: "Another relevant evidence chunk.",
    }

    result = runner.run(
        claims=[claim],
        evidence_by_reference=evidence_by_reference,
    )

    assert len(result.verifications) == 2

    assert result.verifications[0].reference == 1
    assert result.verifications[1].reference == 2


def test_runner_handles_mixed_case():

    runner = CitationVerificationRunner(
        verifier=FakeVerifier()
    )

    claims = [
        Claim(
            text="CrashLoopBackOff may be caused by configuration errors.",
            citations=[1],
        ),

        Claim(
            text="kubectl logs can inspect a failing container.",
            citations=[2],
        ),

        Claim(
            text="HTTP 429 means the Pod ran out of memory.",
            citations=[3],
        ),

        Claim(
            text="This factual claim has no citation.",
            citations=[],
        ),

        Claim(
            text="This claim references missing evidence.",
            citations=[9],
        ),
    ]

    evidence_by_reference = {
        1: "Configuration errors can cause CrashLoopBackOff.",
        2: "Use kubectl logs to inspect container logs.",
        3: "HTTP 429 means Too Many Requests.",
    }

    result = runner.run(
        claims=claims,
        evidence_by_reference=evidence_by_reference,
    )

    assert len(result.verifications) == 3

    assert len(result.uncited_claims) == 1
    assert (
        result.uncited_claims[0].text
        == "This factual claim has no citation."
    )

    assert result.unresolved_references == [9]

    verdicts = [
        verification.verdict
        for verification in result.verifications
    ]

    assert verdicts == [
        SupportVerdict.SUPPORTED,
        SupportVerdict.SUPPORTED,
        SupportVerdict.CONTRADICTED,
    ]