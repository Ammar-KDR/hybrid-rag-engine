from rag.verification.model import Claim
from rag.verification.citation_verifier import GeminiCitationVerifier


def run_case(
    verifier: GeminiCitationVerifier,
    name: str,
    claim: Claim,
    evidence: str,
    expected: str,
):
    print("=" * 70)
    print(name)
    print("=" * 70)

    result = verifier.verify(
        claim=claim,
        reference=claim.citations[0],
        evidence_text=evidence,
    )

    print("CLAIM:")
    print(claim.text)

    print("\nEVIDENCE:")
    print(evidence.strip())

    print("\nEXPECTED:")
    print(expected)

    print("\nACTUAL:")
    print(result.verdict.value)

    print("\nEXPLANATION:")
    print(result.explanation)

    passed = result.verdict.value == expected

    print("\nRESULT:")
    print("PASS" if passed else "FAIL")

    print()

    return passed


def main():

    verifier = GeminiCitationVerifier()

    results = []

    # ---------------------------------------------------------
    # CASE 1 — SUPPORTED
    # ---------------------------------------------------------

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 1 — SUPPORTED",
            claim=Claim(
                text="HTTP 429 means Too Many Requests.",
                citations=[1],
            ),
            evidence="""
HTTP status code 429 indicates Too Many Requests.
""",
            expected="SUPPORTED",
        )
    )

    # ---------------------------------------------------------
    # CASE 2 — CONTRADICTED
    # ---------------------------------------------------------

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 2 — CONTRADICTED",
            claim=Claim(
                text="HTTP 429 means the Pod ran out of memory.",
                citations=[1],
            ),
            evidence="""
HTTP status code 429 indicates Too Many Requests.
""",
            expected="CONTRADICTED",
        )
    )

    # ---------------------------------------------------------
    # CASE 3 — PARTIALLY SUPPORTED
    # ---------------------------------------------------------

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 3 — PARTIALLY SUPPORTED",
            claim=Claim(
                text=(
                    "CrashLoopBackOff may be caused by "
                    "configuration errors and always requires "
                    "deleting the Pod."
                ),
                citations=[1],
            ),
            evidence="""
Configuration errors can cause CrashLoopBackOff.
""",
            expected="PARTIALLY_SUPPORTED",
        )
    )

    # ---------------------------------------------------------
    # CASE 4 — OUTSIDE KNOWLEDGE TRAP
    # ---------------------------------------------------------

    results.append(
        run_case(
            verifier=verifier,
            name="CASE 4 — OUTSIDE KNOWLEDGE TRAP",
            claim=Claim(
                text="Paris is the capital of France.",
                citations=[1],
            ),
            evidence="""
Paris is a major European city.
""",
            expected="UNSUPPORTED",
        )
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    passed = sum(results)
    total = len(results)

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("All controlled citation verification cases passed.")
    else:
        print("Some verifier cases did not match the expected verdict.")


if __name__ == "__main__":
    main()