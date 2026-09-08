from .model import Claim
from ..citation import extract_references


def find_invalid_references(
    claims: list[Claim],
    answer: str,
) -> list[int]:

    answer_references = set(
        extract_references(answer)
    )

    invalid = []
    seen = set()

    for claim in claims:
        for reference in claim.citations:

            if (
                reference not in answer_references
                and reference not in seen
            ):
                invalid.append(reference)
                seen.add(reference)

    return invalid