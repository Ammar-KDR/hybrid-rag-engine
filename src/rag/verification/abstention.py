from .model import (
    AbstentionDecision,
    AbstentionSignals,
    CitationMetrics,
    CitationVerificationResult,
    FaithfulnessSummary,
)


class AbstentionPolicy:

    def decide(
        self,
        faithfulness: FaithfulnessSummary,
        citation_verification: CitationVerificationResult,
        citation_metrics: CitationMetrics,
    ) -> AbstentionDecision:

        reasons = []

        if faithfulness.total_claims == 0:
            reasons.append(
                "No verifiable factual claims were produced."
            )

        if faithfulness.unsupported_claims > 0:
            reasons.append(
                f"{faithfulness.unsupported_claims} factual claim(s) "
                "were unsupported by the supplied evidence."
            )

        if faithfulness.partially_supported_claims > 0:
            reasons.append(
                f"{faithfulness.partially_supported_claims} factual "
                "claim(s) were only partially supported."
            )

        if faithfulness.contradicted_claims > 0:
            reasons.append(
                f"{faithfulness.contradicted_claims} factual claim(s) "
                "were contradicted by the supplied evidence."
            )

        if citation_verification.unresolved_references:
            reasons.append(
                "The answer contained unresolved citation reference(s): "
                + ", ".join(
                    str(reference)
                    for reference
                    in citation_verification.unresolved_references
                )
                + "."
            )

        signals = AbstentionSignals(
            total_claims=faithfulness.total_claims,

            supported_claims=faithfulness.supported_claims,
            partially_supported_claims=(
                faithfulness.partially_supported_claims
            ),
            unsupported_claims=faithfulness.unsupported_claims,
            contradicted_claims=faithfulness.contradicted_claims,

            uncited_claims=len(
                citation_verification.uncited_claims
            ),

            unresolved_references=len(
                citation_verification.unresolved_references
            ),

            citation_precision=citation_metrics.citation_precision,
            citation_coverage=citation_metrics.citation_coverage,
        )

        return AbstentionDecision(
            should_abstain=bool(reasons),
            reasons=reasons,
            signals=signals,
        )