import json
from pathlib import Path

from rag.evaluation.result_aggregator import (
    BenchmarkAggregator,
)


RESULTS_PATH = Path(
    "data/evaluation/day10_structure_cor_v6.jsonl"
)

EXPECTED_TOTAL_CASES = 60


class EvaluationRow(dict):
    """
    Supports both:

        result["correctness_score"]

    and:

        result.correctness_score

    The current BenchmarkAggregator uses both styles.
    """

    def __getattr__(
        self,
        name,
    ):
        try:
            return self[name]

        except KeyError as exc:
            raise AttributeError(
                name
            ) from exc


def load_results(
    path: Path,
) -> list[EvaluationRow]:

    if not path.exists():
        raise FileNotFoundError(
            f"Results file not found: {path}"
        )

    results = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(
                    line
                )

            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line "
                    f"{line_number}"
                ) from exc

            results.append(
                EvaluationRow(
                    data
                )
            )

    return results


def print_correctness_summary(
    results,
):

    scored_results = [
        result
        for result in results
        if (
            result["expected_answerable"]
            and result["correctness_score"]
            is not None
        )
    ]

    unscored_answerable = [
        result
        for result in results
        if (
            result["expected_answerable"]
            and result["correctness_score"]
            is None
        )
    ]


    correctness_values = [
        result["correctness_score"]
        for result in scored_results
    ]


    average_correctness = (
        sum(correctness_values)
        /
        len(correctness_values)
        if correctness_values
        else None
    )


    fully_correct = [
        result
        for result in scored_results
        if (
            result["partially_correct_claims"]
            == 0
            and result["incorrect_claims"]
            == 0
        )
    ]


    fully_correct_rate = (
        len(fully_correct)
        /
        len(scored_results)
        if scored_results
        else None
    )


    total_correct_claims = sum(
        result["correct_claims"]
        for result in scored_results
    )

    total_partial_claims = sum(
        result["partially_correct_claims"]
        for result in scored_results
    )

    total_incorrect_claims = sum(
        result["incorrect_claims"]
        for result in scored_results
    )


    total_claims = (
        total_correct_claims
        +
        total_partial_claims
        +
        total_incorrect_claims
    )


    print()
    print("=" * 70)
    print("CORRECTNESS SUMMARY")
    print("=" * 70)

    print(
        "Scored answerable cases:",
        len(scored_results),
    )

    print(
        "Unscored answerable cases:",
        len(unscored_answerable),
    )

    print(
        "Unscored IDs:",
        [
            result["case_id"]
            for result in unscored_answerable
        ],
    )

    print(
        "Average correctness:",
        (
            round(
                average_correctness,
                4,
            )
            if average_correctness
            is not None
            else "N/A"
        ),
    )

    print(
        "Fully correct answers:",
        len(fully_correct),
    )

    print(
        "Fully correct rate:",
        (
            round(
                fully_correct_rate,
                4,
            )
            if fully_correct_rate
            is not None
            else "N/A"
        ),
    )

    print(
        "Total claims:",
        total_claims,
    )

    print(
        "Correct claims:",
        total_correct_claims,
    )

    print(
        "Partially correct claims:",
        total_partial_claims,
    )

    print(
        "Incorrect claims:",
        total_incorrect_claims,
    )


def main():

    print("=" * 70)
    print(
        "DAY 10 FINAL BENCHMARK VALIDATION"
    )
    print("=" * 70)


    # --------------------------------------------------
    # 1. Load final V3 results
    # --------------------------------------------------

    results = load_results(
        RESULTS_PATH
    )


    print(
        "Loaded cases:",
        len(results),
    )


    if (
        len(results)
        != EXPECTED_TOTAL_CASES
    ):

        raise AssertionError(
            f"Expected "
            f"{EXPECTED_TOTAL_CASES} cases, "
            f"found {len(results)}."
        )


    # --------------------------------------------------
    # 2. Check for duplicate case IDs
    # --------------------------------------------------

    case_ids = [
        result["case_id"]
        for result in results
    ]

    if (
        len(set(case_ids))
        != len(case_ids)
    ):

        raise AssertionError(
            "Duplicate case IDs found."
        )


    print(
        "Dataset integrity: PASS"
    )


    # --------------------------------------------------
    # 3. Demonstrate compatibility
    # --------------------------------------------------

    print(
        "Dictionary access:",
        results[0][
            "correctness_score"
        ],
    )

    print(
        "Attribute access:",
        results[0]
        .correctness_score,
    )


    # --------------------------------------------------
    # 4. Official aggregator
    # --------------------------------------------------

    aggregator = (
        BenchmarkAggregator()
    )

    summary = aggregator.aggregate(
        results
    )


    print()
    print("=" * 70)
    print(
        "OFFICIAL AGGREGATE SUMMARY"
    )
    print("=" * 70)

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )


    # --------------------------------------------------
    # 5. Independent correctness summary
    # --------------------------------------------------

    print_correctness_summary(
        results
    )


    # --------------------------------------------------
    # 6. Final validation
    # --------------------------------------------------

    print()
    print("#" * 70)
    print(
        "DAY 10 FINAL VALIDATION PASSED"
    )
    print("#" * 70)


if __name__ == "__main__":
    main()