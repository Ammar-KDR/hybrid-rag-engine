from .model import (
    Claim,
    FaithfulnessSummary,
    SupportVerdict,
)


class FaithfulnessEvaluator:

    def __init__(self, verifier):
        self.verifier = verifier

    def evaluate(
        self,
        claims: list[Claim],
        evidence_text: str,
    ) -> FaithfulnessSummary:

        claim_results = []

        for claim in claims:
            result = self.verifier.verify(
                claim=claim,
                evidence_text=evidence_text,
            )

            claim_results.append(result)

        supported_claims = sum(
            1
            for result in claim_results
            if result.verdict == SupportVerdict.SUPPORTED
        )

        partially_supported_claims = sum(
            1
            for result in claim_results
            if (
                result.verdict
                == SupportVerdict.PARTIALLY_SUPPORTED
            )
        )

        unsupported_claims = sum(
            1
            for result in claim_results
            if result.verdict == SupportVerdict.UNSUPPORTED
        )

        contradicted_claims = sum(
            1
            for result in claim_results
            if result.verdict == SupportVerdict.CONTRADICTED
        )

        return FaithfulnessSummary(
            claim_results=claim_results,
            total_claims=len(claims),
            supported_claims=supported_claims,
            partially_supported_claims=partially_supported_claims,
            unsupported_claims=unsupported_claims,
            contradicted_claims=contradicted_claims,
        )