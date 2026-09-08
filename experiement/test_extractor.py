from rag.verification.claim_extractor import GeminiClaimExtractor

extractor = GeminiClaimExtractor()

answer = """
CrashLoopBackOff may be caused by configuration errors and
missing environment variables. [1]

Use kubectl logs to inspect the failing container. [2]

HTTP 429 always means the Kubernetes Pod ran out of memory. [3]

This should help.
"""

result = extractor.extract(answer)

for claim in result.claims:
    print("CLAIM:", claim.text)
    print("CITATIONS:", claim.citations)
    print()