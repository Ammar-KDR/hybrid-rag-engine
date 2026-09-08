from rag.verification.model import (
    Claim,
    CitationVerification,
    CitationVerificationResult,
    CitationMetrics,
    SupportVerdict,
)

from rag.verification.metrics import CitationMetricsCalculator


def make_verification(
    claim_text: str,
    reference: int,
    verdict: SupportVerdict,
) -> CitationVerification:

    return CitationVerification(
        claim_text=claim_text,
        reference=reference,
        verdict=verdict,
        explanation="Test verification.",
    )


def test_all_supported_gives_full_precision_and_coverage():

    claims = [
        Claim(
            text="Claim A",
            citations=[1],
        ),
        Claim(
            text="Claim B",
            citations=[2],
        ),
    ]

    verification_result = CitationVerificationResult(
        verifications=[
            make_verification(
                "Claim A",
                1,
                SupportVerdict.SUPPORTED,
            ),
            make_verification(
                "Claim B",
                2,
                SupportVerdict.SUPPORTED,
            ),
        ],
        uncited_claims=[],
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    assert metrics.citation_precision == 1.0
    assert metrics.citation_coverage == 1.0

    assert metrics.total_verifications == 2
    assert metrics.supported_verifications == 2
    assert metrics.partially_supported_verifications == 0
    assert metrics.unsupported_verifications == 0
    assert metrics.contradicted_verifications == 0

    assert metrics.total_claims == 2
    assert metrics.adequately_cited_claims == 2
    assert metrics.uncited_claims == 0


def test_one_supported_and_one_unsupported_lowers_precision_and_coverage():

    claims = [
        Claim(
            text="Claim A",
            citations=[1],
        ),
        Claim(
            text="Claim B",
            citations=[2],
        ),
    ]

    verification_result = CitationVerificationResult(
        verifications=[
            make_verification(
                "Claim A",
                1,
                SupportVerdict.SUPPORTED,
            ),
            make_verification(
                "Claim B",
                2,
                SupportVerdict.UNSUPPORTED,
            ),
        ],
        uncited_claims=[],
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    assert metrics.citation_precision == 0.5
    assert metrics.citation_coverage == 0.5

    assert metrics.supported_verifications == 1
    assert metrics.unsupported_verifications == 1


def test_good_and_bad_citation_for_same_claim_penalizes_precision_but_keeps_coverage():

    claims = [
        Claim(
            text="Claim A",
            citations=[1, 2],
        ),
    ]

    verification_result = CitationVerificationResult(
        verifications=[
            make_verification(
                "Claim A",
                1,
                SupportVerdict.SUPPORTED,
            ),
            make_verification(
                "Claim A",
                2,
                SupportVerdict.UNSUPPORTED,
            ),
        ],
        uncited_claims=[],
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    assert metrics.citation_precision == 0.5

    # The claim is still covered because at least
    # one attached citation fully supports it.
    assert metrics.citation_coverage == 1.0

    assert metrics.total_verifications == 2
    assert metrics.supported_verifications == 1
    assert metrics.unsupported_verifications == 1

    assert metrics.total_claims == 1
    assert metrics.adequately_cited_claims == 1


def test_partial_support_does_not_count_as_strict_precision_success():

    claims = [
        Claim(
            text="Claim A",
            citations=[1],
        ),
    ]

    verification_result = CitationVerificationResult(
        verifications=[
            make_verification(
                "Claim A",
                1,
                SupportVerdict.PARTIALLY_SUPPORTED,
            ),
        ],
        uncited_claims=[],
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    assert metrics.citation_precision == 0.0
    assert metrics.citation_coverage == 0.0

    assert metrics.partially_supported_verifications == 1
    assert metrics.adequately_cited_claims == 0


def test_contradicted_citation_counts_as_failure():

    claims = [
        Claim(
            text="Claim A",
            citations=[1],
        ),
    ]

    verification_result = CitationVerificationResult(
        verifications=[
            make_verification(
                "Claim A",
                1,
                SupportVerdict.CONTRADICTED,
            ),
        ],
        uncited_claims=[],
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    assert metrics.citation_precision == 0.0
    assert metrics.citation_coverage == 0.0

    assert metrics.contradicted_verifications == 1


def test_uncited_claim_reduces_coverage_but_not_precision():

    cited_claim = Claim(
        text="Claim A",
        citations=[1],
    )

    uncited_claim = Claim(
        text="Claim B",
        citations=[],
    )

    claims = [
        cited_claim,
        uncited_claim,
    ]

    verification_result = CitationVerificationResult(
        verifications=[
            make_verification(
                "Claim A",
                1,
                SupportVerdict.SUPPORTED,
            ),
        ],
        uncited_claims=[
            uncited_claim,
        ],
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    # The only citation relationship is valid.
    assert metrics.citation_precision == 1.0

    # But only one of the two factual claims is adequately cited.
    assert metrics.citation_coverage == 0.5

    assert metrics.uncited_claims == 1
    assert metrics.adequately_cited_claims == 1


def test_unresolved_reference_does_not_create_verification_and_claim_is_not_covered():

    claims = [
        Claim(
            text="Claim A",
            citations=[9],
        ),
    ]

    verification_result = CitationVerificationResult(
        verifications=[],
        uncited_claims=[],
        unresolved_references=[9],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    # No semantic citation relationship could actually be verified.
    assert metrics.citation_precision is None

    # The factual claim still lacks an adequately supported citation.
    assert metrics.citation_coverage == 0.0

    assert metrics.total_verifications == 0
    assert metrics.adequately_cited_claims == 0


def test_no_verifications_returns_none_precision():

    claims = [
        Claim(
            text="Claim A",
            citations=[],
        ),
    ]

    verification_result = CitationVerificationResult(
        verifications=[],
        uncited_claims=claims,
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=claims,
        verification_result=verification_result,
    )

    assert metrics.citation_precision is None
    assert metrics.citation_coverage == 0.0


def test_no_claims_returns_none_coverage_and_precision():

    verification_result = CitationVerificationResult(
        verifications=[],
        uncited_claims=[],
        unresolved_references=[],
    )

    calculator = CitationMetricsCalculator()

    metrics = calculator.calculate(
        claims=[],
        verification_result=verification_result,
    )

    assert metrics.citation_precision is None
    assert metrics.citation_coverage is None

    assert metrics.total_claims == 0
    assert metrics.total_verifications == 0