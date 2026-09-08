from rag.generation.model import (
    ContextBlock,
    GeneratedAnswer,
    Citation,
)

from rag.verification.claim_extractor import (
    GeminiClaimExtractor,
)

from rag.verification.citation_verifier import (
    GeminiCitationVerifier,
)

from rag.verification.runner import (
    CitationVerificationRunner,
)

from rag.verification.metrics import (
    CitationMetricsCalculator,
)

from rag.verification.faithfulness_verifier import (
    GeminiFaithfulnessVerifier,
)

from rag.verification.faithfulness import (
    FaithfulnessEvaluator,
)

from rag.verification.abstention import (
    AbstentionPolicy,
)

from rag.verification.pipeline import (
    AnswerVerificationPipeline,
)


# ============================================================
# CONFIG
# ============================================================

VERIFICATION_MODEL = "gemini-3.8-flash"


# ============================================================
# BUILD VERIFICATION PIPELINE
# ============================================================

def build_verification_pipeline():

    claim_extractor = GeminiClaimExtractor(
        model=VERIFICATION_MODEL
    )

    citation_verifier = GeminiCitationVerifier(
        model=VERIFICATION_MODEL
    )

    citation_runner = CitationVerificationRunner(
        verifier=citation_verifier
    )

    metrics_calculator = CitationMetricsCalculator()

    faithfulness_verifier = GeminiFaithfulnessVerifier(
        model=VERIFICATION_MODEL
    )

    faithfulness_evaluator = FaithfulnessEvaluator(
        verifier=faithfulness_verifier
    )

    abstention_policy = AbstentionPolicy()

    return AnswerVerificationPipeline(
        claim_extractor=claim_extractor,
        citation_runner=citation_runner,
        metrics_calculator=metrics_calculator,
        faithfulness_evaluator=faithfulness_evaluator,
        abstention_policy=abstention_policy,
    )


# ============================================================
# DISPLAY
# ============================================================

def print_verified_result(
    name: str,
    verified,
    expected_abstention: bool,
):

    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

    print("\nQUESTION:")
    print(
        verified.generated_answer.question
    )

    print("\nORIGINAL GENERATED ANSWER:")
    print(
        verified.generated_answer.answer
    )

    print("\nFINAL ANSWER:")
    print(
        verified.final_answer
    )

    print("\nCLAIMS:")

    if not verified.claims.claims:
        print("No factual claims extracted.")

    for index, claim in enumerate(
        verified.claims.claims,
        start=1,
    ):
        print(
            f"{index}. {claim.text}"
        )
        print(
            f"   Citations: {claim.citations}"
        )

    print("\nCITATION VERIFICATION:")

    if not verified.citation_verification.verifications:
        print(
            "No claim/citation relationships verified."
        )

    for verification in (
        verified.citation_verification.verifications
    ):
        print(
            f"- Claim: {verification.claim_text}"
        )
        print(
            f"  Reference: [{verification.reference}]"
        )
        print(
            f"  Verdict: {verification.verdict.value}"
        )
        print(
            f"  Explanation: {verification.explanation}"
        )

    print("\nUNCITED CLAIMS:")

    if verified.citation_verification.uncited_claims:
        for claim in (
            verified.citation_verification.uncited_claims
        ):
            print(
                f"- {claim.text}"
            )
    else:
        print("None")

    print("\nUNRESOLVED REFERENCES:")
    print(
        verified.citation_verification.unresolved_references
    )

    metrics = verified.citation_metrics

    print("\nCITATION METRICS:")
    print(
        "Precision:",
        metrics.citation_precision,
    )
    print(
        "Coverage:",
        metrics.citation_coverage,
    )

    print(
        "Supported citation relationships:",
        metrics.supported_verifications,
    )

    print(
        "Partially supported citation relationships:",
        metrics.partially_supported_verifications,
    )

    print(
        "Unsupported citation relationships:",
        metrics.unsupported_verifications,
    )

    print(
        "Contradicted citation relationships:",
        metrics.contradicted_verifications,
    )

    print(
        "Adequately cited claims:",
        f"{metrics.adequately_cited_claims}"
        f"/{metrics.total_claims}",
    )

    faithfulness = verified.faithfulness

    print("\nFAITHFULNESS:")
    print(
        "Total claims:",
        faithfulness.total_claims,
    )
    print(
        "Supported:",
        faithfulness.supported_claims,
    )
    print(
        "Partially supported:",
        faithfulness.partially_supported_claims,
    )
    print(
        "Unsupported:",
        faithfulness.unsupported_claims,
    )
    print(
        "Contradicted:",
        faithfulness.contradicted_claims,
    )

    print("\nCLAIM FAITHFULNESS:")

    if not faithfulness.claim_results:
        print("No claim faithfulness results.")

    for result in faithfulness.claim_results:
        print(
            f"- {result.claim_text}"
        )
        print(
            f"  Verdict: {result.verdict.value}"
        )
        print(
            f"  Explanation: {result.explanation}"
        )

    print("\nABSTENTION:")
    print(
        "Should abstain:",
        verified.abstention.should_abstain,
    )

    print("\nABSTENTION REASONS:")

    if verified.abstention.reasons:
        for reason in verified.abstention.reasons:
            print(
                f"- {reason}"
            )
    else:
        print("None")

    print("\nABSTENTION SIGNALS:")
    print(
        verified.abstention.signals
    )

    print("\nVERIFICATION MODEL:")
    print(
        verified.claims.model
    )

    print("\nCLAIM EXTRACTION LATENCY:")
    print(
        f"{verified.claims.latency_ms:.2f} ms"
    )

    print("\nTOTAL VERIFICATION PIPELINE LATENCY:")
    print(
        f"{verified.verification_latency_ms:.2f} ms"
    )

    actual = (
        verified.abstention.should_abstain
    )

    passed = (
        actual == expected_abstention
    )

    print("\nEXPECTED ABSTENTION:")
    print(expected_abstention)

    print("\nACTUAL ABSTENTION:")
    print(actual)

    print("\nRESULT:")
    print(
        "PASS"
        if passed
        else "FAIL"
    )

    return passed


# ============================================================
# CASE 1
#
# Strong answerable query.
#
# Expected:
# DO NOT ABSTAIN
# ============================================================



# ============================================================
# CASE 3
#
# Weak evidence.
#
# Evidence discusses resource limits but does not establish
# a specific universal production recommendation.
#
# Generated answer intentionally overreaches.
#
# Expected:
# ABSTAIN
# ============================================================

def case_weak_evidence(
    pipeline: AnswerVerificationPipeline,
):

    evidence = [
        ContextBlock(
            reference=1,
            chunk_id="k8s-resource-001",
            text=(
                "Kubernetes resource requests and limits "
                "control how CPU and memory resources are "
                "allocated to containers."
            ),
            source="kubernetes_resources.md",
            heading_path=[
                "Kubernetes",
                "Resource Management",
            ],
        ),

        ContextBlock(
            reference=2,
            chunk_id="k8s-oom-001",
            text=(
                "A container may be terminated with OOMKilled "
                "when it exceeds its available memory."
            ),
            source="kubernetes_resources.md",
            heading_path=[
                "Kubernetes",
                "Memory",
            ],
        ),
    ]

    generated = GeneratedAnswer(
        question=(
            "How should I optimize Kubernetes resource "
            "limits for a production workload?"
        ),

        answer=(
            "For production workloads, CPU limits should always "
            "be set to twice the CPU request and memory limits "
            "should always be set 25% above observed usage. [1][2]"
        ),

        citations=[
            Citation(
                reference=1,
                chunk_id="k8s-resource-001",
                source="kubernetes_resources.md",
                heading_path=[
                    "Kubernetes",
                    "Resource Management",
                ],
            ),

            Citation(
                reference=2,
                chunk_id="k8s-oom-001",
                source="kubernetes_resources.md",
                heading_path=[
                    "Kubernetes",
                    "Memory",
                ],
            ),
        ],

        unresolved_references=[],

        evidence=evidence,

        model="behavioral-test-generator",
    )

    verified = pipeline.verify(
        generated
    )

    return print_verified_result(
        name=(
            "CASE 3 — WEAK EVIDENCE / "
            "OVERREACHING RECOMMENDATION"
        ),
        verified=verified,
        expected_abstention=True,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("DAY 9 — ANSWER VERIFICATION PIPELINE")
    print("=" * 80)

    print(
        f"\nVerification model: {VERIFICATION_MODEL}"
    )

    pipeline = build_verification_pipeline()

    results = []

    results.append(
        

    results.append(
        case_weak_evidence(
            pipeline
        ))
    )

    passed = sum(results)
    total = len(results)

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(
        f"Passed: {passed}/{total}"
    )

    print()

    print(
        "CASE 1 — Answerable Kubernetes query:",
        "PASS" if results[0] else "FAIL",
    )

    print(
        "CASE 2 — Out-of-corpus AWS Lambda query:",
        "PASS" if results[1] else "FAIL",
    )

    print(
        "CASE 3 — Weak-evidence Kubernetes query:",
        "PASS" if results[2] else "FAIL",
    )

    print()

    if passed == total:
        print(
            "All controlled Day 9 verification/"
            "abstention cases passed."
        )
    else:
        print(
            "One or more Day 9 behavioral cases "
            "require inspection."
        )


if __name__ == "__main__":
    main()