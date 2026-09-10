import json

from rag.evaluation.result_aggregator import (
    BenchmarkAggregator,
)

from rag.evaluation.failure_classifier import (
    FailureClassifier,
)

RESULT_PATH = (
    "data/evaluation/"
    "day10_structure_corr_v.jsonl"
)


def main():

    aggregator = BenchmarkAggregator()

    results = aggregator.load_results(
        RESULT_PATH
    )

    report = aggregator.aggregate(
        results
    )
    classifier = FailureClassifier()

    failure_counts = {}
    failure_cases = {}


    for result in results:

        classification = classifier.classify(
            result
        )

        for failure_type in (
            classification.failure_types
        ):

            failure_counts[failure_type] = (
                failure_counts.get(
                    failure_type,
                    0,
                )
                +
                1
            )

            if failure_type not in failure_cases:

                failure_cases[
                    failure_type
                ] = []

            failure_cases[
                failure_type
            ].append(
                classification.case_id
            )
    print(
        json.dumps(
            report,
            indent=4,
        )
    )
    print()
    print("=" * 70)
    print("FAILURE TAXONOMY")
    print("=" * 70)

    print(
        json.dumps(
            {
                "counts": failure_counts,
                "cases": failure_cases,
            },
            indent=4,
        )
    )


if __name__ == "__main__":
    main()