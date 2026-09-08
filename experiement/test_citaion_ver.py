from rag.citation import extract_references
from rag.verification.model import Claim
from rag.verification.validation import find_invalid_references


def test_extract_single_reference():
    answer = "CrashLoopBackOff may be caused by configuration errors. [1]"

    references = extract_references(answer)

    assert references == [1]


def test_extract_multiple_references():
    answer = """
    CrashLoopBackOff may be caused by configuration errors. [1]
    Use kubectl logs to inspect the container. [2]
    HTTP 429 means Too Many Requests. [3]
    """

    references = extract_references(answer)

    assert references == [1, 2, 3]


def test_extract_multiple_citations_attached_to_same_claim():
    answer = (
        "The failure may be caused by DNS problems "
        "or connection pool exhaustion. [1][3]"
    )

    references = extract_references(answer)

    assert references == [1, 3]


def test_extract_references_removes_duplicates():
    answer = """
    First claim. [1]
    Second claim. [2]
    Third claim. [1]
    """

    references = extract_references(answer)

    assert references == [1, 2]


def test_extract_references_preserves_first_seen_order():
    answer = """
    First claim. [3]
    Second claim. [1]
    Third claim. [2]
    Fourth claim. [3]
    """

    references = extract_references(answer)

    assert references == [3, 1, 2]


def test_extract_references_returns_empty_list_when_no_citations():
    answer = "kubectl logs can inspect container output."

    references = extract_references(answer)

    assert references == []


def test_find_invalid_references_returns_empty_when_all_are_valid():
    answer = """
    CrashLoopBackOff may be caused by configuration errors. [1]
    Use kubectl logs to inspect the container. [2]
    """

    claims = [
        Claim(
            text="CrashLoopBackOff may be caused by configuration errors.",
            citations=[1],
        ),
        Claim(
            text="kubectl logs can be used to inspect the container.",
            citations=[2],
        ),
    ]

    invalid = find_invalid_references(
        claims=claims,
        answer=answer,
    )

    assert invalid == []


def test_find_invalid_reference_invented_by_claim_extractor():
    answer = """
    CrashLoopBackOff may be caused by configuration errors. [1]
    """

    claims = [
        Claim(
            text="CrashLoopBackOff may be caused by configuration errors.",
            citations=[7],
        ),
    ]

    invalid = find_invalid_references(
        claims=claims,
        answer=answer,
    )

    assert invalid == [7]


def test_reference_is_not_invalid_if_it_appeared_in_original_answer():
    answer = """
    CrashLoopBackOff may be caused by configuration errors. [9]
    """

    claims = [
        Claim(
            text="CrashLoopBackOff may be caused by configuration errors.",
            citations=[9],
        ),
    ]

    invalid = find_invalid_references(
        claims=claims,
        answer=answer,
    )

    assert invalid == []