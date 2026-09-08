from rag.verification.model import (
    Claim,
    SupportVerdict,
)
from rag.verification.faithfulness_verifier import GeminiFaithfulnessVerifier


def run_case(
    verifier: GeminiFaithfulnessVerifier,
    name: str,
    claim: Claim,
    evidence: str,
    expected: SupportVerdict,
) -> bool:

    print("=" * 70)
    print(name)
    print("=" * 70)

    result = verifier.verify(
        claim=claim,
        evidence_text=evidence,
    )

    print("CLAIM:")
    print(claim.text)

    print("\nCITATIONS:")
    print(claim.citations)

    print("\nEVIDENCE:")
    print(evidence.strip())

    print("\nEXPECTED:")
    print(expected.value)

    print("\nACTUAL:")
    print(result.verdict.value)

    print("\nEXPLANATION:")
    print(result.explanation)

    passed = result.verdict == expected

    print("\nRESULT:")
    print("PASS" if passed else "FAIL")
    print()

    return passed


def main():

    verifier = GeminiFaithfulnessVerifier(
        model="gemini-3.6-flash"
    )

    results = []

    
    # =========================================================
    # CASE 5 — Contradicted claim
    # =========================================================

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 5 — CONTRADICTED CLAIM",
            claim=Claim(
                text="HTTP 429 means Internal Server Error.",
                citations=[1],
            ),
            evidence="""
[1]
HTTP 429 means Too Many Requests.
""",
            expected=SupportVerdict.CONTRADICTED,
        )
    )

    # =========================================================
    # CASE 6 — Partially supported
    # =========================================================

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 6 — PARTIALLY SUPPORTED",
            claim=Claim(
                text=(
                    "Configuration errors can cause "
                    "CrashLoopBackOff and deleting the Pod "
                    "is always required."
                ),
                citations=[1],
            ),
            evidence="""
[1]
Configuration errors can cause CrashLoopBackOff.
""",
            expected=SupportVerdict.PARTIALLY_SUPPORTED,
        )
    )

    # =========================================================
    # CASE 7 — Outside knowledge trap
    #
    # Gemini knows the claim is true.
    # But the evidence does not establish it.
    # Therefore faithfulness must be UNSUPPORTED.
    # =========================================================

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 7 — OUTSIDE KNOWLEDGE TRAP",
            claim=Claim(
                text="Paris is the capital of France.",
                citations=[1],
            ),
            evidence="""
[1]
Paris is a major European city.
""",
            expected=SupportVerdict.UNSUPPORTED,
        )
    )

    # =========================================================
    # CASE 8 — Topically related but not sufficient
    #
    # This checks whether Gemini confuses semantic similarity
    # with actual support.
    # =========================================================

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 8 — TOPICALLY RELATED BUT UNSUPPORTED",
            claim=Claim(
                text=(
                    "The application failed because "
                    "DNS returned NXDOMAIN."
                ),
                citations=[1],
            ),
            evidence="""
[1]
NXDOMAIN indicates that a DNS name could not be resolved.

[2]
DNS failures can prevent applications from reaching services.
""",
            expected=SupportVerdict.UNSUPPORTED,
        )
    )

    # =========================================================
    # SUMMARY
    # =========================================================

    passed = sum(results)
    total = len(results)

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print(
            "All controlled Gemini faithfulness cases passed."
        )
    else:
        print(
            "Some Gemini faithfulness cases did not match "
            "the expected verdict."
        )


if __name__ == "__main__":
    main()