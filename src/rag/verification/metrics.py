from .model import (
    CitationVerificationResult,
    CitationMetrics,
    Claim,
    SupportVerdict,
)


class CitationMetricsCalculator:

    def calculate(
        self,
        claims: list[Claim],
        verification_result: CitationVerificationResult,
    ) -> CitationMetrics:

        verifications = (
            verification_result.verifications
        )

        total_verifications = len(verifications)

        supported_verifications = sum(
            1
            for verification in verifications
            if verification.verdict == SupportVerdict.SUPPORTED
        )

        partially_supported_verifications = sum(
            1
            for verification in verifications
            if (
                verification.verdict
                == SupportVerdict.PARTIALLY_SUPPORTED
            )
        )

        unsupported_verifications = sum(
            1
            for verification in verifications
            if verification.verdict == SupportVerdict.UNSUPPORTED
        )

        contradicted_verifications = sum(
            1
            for verification in verifications
            if verification.verdict == SupportVerdict.CONTRADICTED
        )

        if total_verifications == 0:
            citation_precision = None
        else:
            citation_precision = (
                supported_verifications
                / total_verifications
            )

        total_claims = len(claims)

        supported_claim_texts = {
            verification.claim_text
            for verification in verifications
            if verification.verdict == SupportVerdict.SUPPORTED
        }

        adequately_cited_claims = sum(
            1
            for claim in claims
            if claim.text in supported_claim_texts
        )

        if total_claims == 0:
            citation_coverage = None
        else:
            citation_coverage = (
                adequately_cited_claims
                / total_claims
            )

        return CitationMetrics(
            citation_precision=citation_precision,
            citation_coverage=citation_coverage,

            total_verifications=total_verifications,
            supported_verifications=supported_verifications,
            partially_supported_verifications=(
                partially_supported_verifications
            ),
            unsupported_verifications=unsupported_verifications,
            contradicted_verifications=contradicted_verifications,

            total_claims=total_claims,
            adequately_cited_claims=adequately_cited_claims,
            uncited_claims=len(
                verification_result.uncited_claims
            ),
        )