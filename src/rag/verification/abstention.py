from .model import (
    AbstentionDecision,
    AbstentionDecisionType,
    AbstentionSignals,
    CitationMetrics,
    CitationVerificationResult,
    FaithfulnessSummary,
)


class AbstentionPolicy:

    SUPPORTED_WEIGHT = 1.0
    PARTIALLY_SUPPORTED_WEIGHT = 0.5
    UNSUPPORTED_WEIGHT = 0.0
    CONTRADICTED_WEIGHT = -1.0


    def decide(
        self,
        faithfulness: FaithfulnessSummary,
        citation_verification: CitationVerificationResult,
        citation_metrics: CitationMetrics,
    ) -> AbstentionDecision:

        reasons = []

        total_claims = faithfulness.total_claims


        # --------------------------------------------------
        # 1. Claim ratios
        # --------------------------------------------------

        if total_claims == 0:

            supported_ratio = None
            partially_supported_ratio = None
            unsupported_ratio = None
            contradicted_ratio = None
            faithfulness_score = None

        else:

            supported_ratio = (
                faithfulness.supported_claims
                / total_claims
            )

            partially_supported_ratio = (
                faithfulness.partially_supported_claims
                / total_claims
            )

            unsupported_ratio = (
                faithfulness.unsupported_claims
                / total_claims
            )

            contradicted_ratio = (
                faithfulness.contradicted_claims
                / total_claims
            )


            # ----------------------------------------------
            # Weighted faithfulness score
            # ----------------------------------------------

            weighted_sum = (
                faithfulness.supported_claims
                * self.SUPPORTED_WEIGHT

                + faithfulness.partially_supported_claims
                * self.PARTIALLY_SUPPORTED_WEIGHT

                + faithfulness.unsupported_claims
                * self.UNSUPPORTED_WEIGHT

                + faithfulness.contradicted_claims
                * self.CONTRADICTED_WEIGHT
            )

            faithfulness_score = (
                weighted_sum
                / total_claims
            )


        # --------------------------------------------------
        # 2. Hard abstention conditions
        # --------------------------------------------------

        if total_claims == 0:

            reasons.append(
                "No verifiable factual claims were produced."
            )


        if faithfulness.unsupported_claims > 0:

            reasons.append(
                f"{faithfulness.unsupported_claims} factual claim(s) "
                "were unsupported by the supplied evidence."
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


        # --------------------------------------------------
        # 3. Decision
        # --------------------------------------------------

        if reasons:

            decision = (
                AbstentionDecisionType.ABSTAIN
            )

            should_abstain = True


        elif faithfulness.partially_supported_claims > 0:

            decision = (
                AbstentionDecisionType.ACCEPT_WITH_WARNING
            )

            should_abstain = False


        else:

            decision = (
                AbstentionDecisionType.ACCEPT
            )

            should_abstain = False


        # --------------------------------------------------
        # 4. Signals
        # --------------------------------------------------

        signals = AbstentionSignals(
            total_claims=total_claims,

            supported_claims=faithfulness.supported_claims,

            partially_supported_claims=(
                faithfulness.partially_supported_claims
            ),

            unsupported_claims=(
                faithfulness.unsupported_claims
            ),

            contradicted_claims=(
                faithfulness.contradicted_claims
            ),

            uncited_claims=len(
                citation_verification.uncited_claims
            ),

            unresolved_references=len(
                citation_verification.unresolved_references
            ),

            citation_precision=(
                citation_metrics.citation_precision
            ),

            citation_coverage=(
                citation_metrics.citation_coverage
            ),

            faithfulness_score=faithfulness_score,

            supported_ratio=supported_ratio,

            partially_supported_ratio=(
                partially_supported_ratio
            ),

            unsupported_ratio=unsupported_ratio,

            contradicted_ratio=contradicted_ratio,
        )


        return AbstentionDecision(
            should_abstain=should_abstain,
            decision=decision,
            reasons=reasons,
            signals=signals,
        )