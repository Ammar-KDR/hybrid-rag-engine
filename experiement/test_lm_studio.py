from rag.verification.faithfulness_verifier import (
    LMStudioFaithfulnessVerifier,
)

from rag.verification.model import Claim
from rag.config import settings

verifier = LMStudioFaithfulnessVerifier(
    model=settings.LM_STUDIO_MODEL
)


tests = [
    {
        "expected": "SUPPORTED",
        "claim": (
            "HTTP 429 means the client exceeded "
            "the allowed request rate."
        ),
        "evidence": (
            "HTTP 429 indicates that the client exceeded "
            "the allowed request rate."
        ),
    },

    {
        "expected": "PARTIALLY_SUPPORTED",
        "claim": (
            "HTTP 429 means the client exceeded the request "
            "rate and the server is permanently unavailable."
        ),
        "evidence": (
            "HTTP 429 indicates that the client exceeded "
            "the allowed request rate."
        ),
    },

    {
        "expected": "UNSUPPORTED",
        "claim": (
            "HTTP 429 is caused by DNS resolution failure."
        ),
        "evidence": (
            "HTTP 429 indicates that the client exceeded "
            "the allowed request rate."
        ),
    },

    {
        "expected": "CONTRADICTED",
        "claim": (
            "HTTP 429 means the client is below "
            "the allowed request rate."
        ),
        "evidence": (
            "HTTP 429 indicates that the client exceeded "
            "the allowed request rate."
        ),
    },
]


for test in tests:

    result = verifier.verify(
        claim=Claim(
            text=test["claim"],
            citations=[],
        ),
        evidence_text=test["evidence"],
    )

    print("=" * 60)
    print("Expected:", test["expected"])
    print("Actual:  ", result.verdict.value)
    print("Explanation:", result.explanation)