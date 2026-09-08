from rag.verification.abstention import AbstentionPolicy

from rag.verification.model import (
    Claim,
    CitationMetrics,
    CitationVerificationResult,
    FaithfulnessSummary,
)


def make_metrics(
    precision=1.0,
    coverage=1.0,
    total_claims=1,
    adequately_cited_claims=1,
    uncited_claims=0,
):
    return CitationMetrics(
        citation_precision=precision,
        citation_coverage=coverage,

        total_verifications=1,
        supported_verifications=1,
        partially_supported_verifications=0,
        unsupported_verifications=0,
        contradicted_verifications=0,

        total_claims=total_claims,
        adequately_cited_claims=adequately_cited_claims,
        uncited_claims=uncited_claims,
    )


def make_faithfulness(
    total=1,
    supported=1,
    partial=0,
    unsupported=0,
    contradicted=0,
):
    return FaithfulnessSummary(
        claim_results=[],
        total_claims=total,
        supported_claims=supported,
        partially_supported_claims=partial,
        unsupported_claims=unsupported,
        contradicted_claims=contradicted,
    )


def test_fully_supported_answer_does_not_abstain():

    policy = AbstentionPolicy()

    decision = policy.decide(
        faithfulness=make_faithfulness(),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[],
        ),
        citation_metrics=make_metrics(),
    )

    assert decision.should_abstain is False
    assert decision.reasons == []


def test_unsupported_claim_causes_abstention():

    policy = AbstentionPolicy()

    decision = policy.decide(
        faithfulness=make_faithfulness(
            supported=0,
            unsupported=1,
        ),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[],
        ),
        citation_metrics=make_metrics(),
    )

    assert decision.should_abstain is True

    assert any(
        "unsupported" in reason.lower()
        for reason in decision.reasons
    )


def test_partial_claim_causes_abstention():

    policy = AbstentionPolicy()

    decision = policy.decide(
        faithfulness=make_faithfulness(
            supported=0,
            partial=1,
        ),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[],
        ),
        citation_metrics=make_metrics(),
    )

    assert decision.should_abstain is True

    assert any(
        "partially" in reason.lower()
        for reason in decision.reasons
    )


def test_contradicted_claim_causes_abstention():

    policy = AbstentionPolicy()

    decision = policy.decide(
        faithfulness=make_faithfulness(
            supported=0,
            contradicted=1,
        ),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[],
        ),
        citation_metrics=make_metrics(),
    )

    assert decision.should_abstain is True

    assert any(
        "contradicted" in reason.lower()
        for reason in decision.reasons
    )


def test_unresolved_reference_causes_abstention():

    policy = AbstentionPolicy()

    decision = policy.decide(
        faithfulness=make_faithfulness(),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[9],
        ),
        citation_metrics=make_metrics(),
    )

    assert decision.should_abstain is True
    assert decision.signals.unresolved_references == 1


def test_uncited_but_faithful_claim_does_not_abstain():

    policy = AbstentionPolicy()

    uncited_claim = Claim(
        text="kubectl logs can inspect container output.",
        citations=[],
    )

    decision = policy.decide(
        faithfulness=make_faithfulness(
            total=1,
            supported=1,
        ),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[uncited_claim],
            unresolved_references=[],
        ),
        citation_metrics=make_metrics(
            precision=None,
            coverage=0.0,
            adequately_cited_claims=0,
            uncited_claims=1,
        ),
    )

    assert decision.should_abstain is False
    assert decision.signals.uncited_claims == 1
    assert decision.signals.citation_coverage == 0.0


def test_no_factual_claims_causes_abstention():

    policy = AbstentionPolicy()

    decision = policy.decide(
        faithfulness=make_faithfulness(
            total=0,
            supported=0,
        ),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[],
        ),
        citation_metrics=make_metrics(
            precision=None,
            coverage=None,
            total_claims=0,
            adequately_cited_claims=0,
        ),
    )

    assert decision.should_abstain is True

    assert any(
        "no verifiable factual claims" in reason.lower()
        for reason in decision.reasons
    )


def test_multiple_failures_preserve_multiple_reasons():

    policy = AbstentionPolicy()

    decision = policy.decide(
        faithfulness=make_faithfulness(
            total=3,
            supported=0,
            partial=1,
            unsupported=1,
            contradicted=1,
        ),
        citation_verification=CitationVerificationResult(
            verifications=[],
            uncited_claims=[],
            unresolved_references=[9],
        ),
        citation_metrics=make_metrics(),
    )

    assert decision.should_abstain is True

    assert len(decision.reasons) == 4

    assert decision.signals.partially_supported_claims == 1
    assert decision.signals.unsupported_claims == 1
    assert decision.signals.contradicted_claims == 1
    assert decision.signals.unresolved_references == 1