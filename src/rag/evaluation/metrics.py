def hit_rate_at_k(
    retrieved_ids: list[str],
    expected_ids: list[str],
    k: int,
) -> float:

    retrieved_top_k = retrieved_ids[:k]

    for chunk_id in expected_ids:
        if chunk_id in retrieved_top_k:
            return 1.0

    return 0.0

def recall_at_k(
    retrieved_ids: list[str],
    expected_ids: list[str],
    k: int,
) -> float:

    retrieved_top_k = set(
        retrieved_ids[:k]
    )

    expected = set(expected_ids)

    if not expected:
        return 0.0

    relevant_found = (
        retrieved_top_k.intersection(expected)
    )

    return (
        len(relevant_found)
        /
        len(expected)
    )

def precision_at_k(
    retrieved_ids: list[str],
    expected_ids: list[str],
    k: int,
) -> float:

    retrieved_top_k = set(
        retrieved_ids[:k]
    )

    expected = set(expected_ids)

    if not retrieved_top_k:
        return 0.0

    relevant_retrieved = (
        retrieved_top_k.intersection(expected)
    )

    return (
        len(relevant_retrieved)
        /
        len(retrieved_top_k)
    )
def reciprocal_rank(
    retrieved_ids: list[str],
    expected_ids: list[str],
):
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in expected_ids:
            return 1 / rank

    return 0.0