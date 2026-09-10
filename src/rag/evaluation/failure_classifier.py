from dataclasses import dataclass


@dataclass(frozen=True)
class FailureClassification:

    case_id: str
    failure_types: list[str]


class FailureClassifier:

    def classify(
        self,
        result: dict,
    ) -> FailureClassification:

        failure_types = []

        answerable = result[
            "expected_answerable"
        ]

        should_abstain = result[
            "should_abstain"
        ]


        # ----------------------------------------------
        # Candidate retrieval
        # ----------------------------------------------

        if (
            answerable
            and
            result["candidate_hit"] is False
        ):

            failure_types.append(
                "CANDIDATE_RETRIEVAL_FAILURE"
            )


        # ----------------------------------------------
        # Reranking / context selection
        # ----------------------------------------------

        if (
            answerable
            and
            result["candidate_hit"] is True
            and
            result["final_hit"] is False
        ):

            failure_types.append(
                "FINAL_CONTEXT_SELECTION_FAILURE"
            )


        # ----------------------------------------------
        # False abstention
        # ----------------------------------------------

        if (
            answerable
            and
            should_abstain
        ):

            failure_types.append(
                "FALSE_ABSTENTION"
            )


        # ----------------------------------------------
        # False answer
        # ----------------------------------------------

        if (
            not answerable
            and
            not should_abstain
        ):

            failure_types.append(
                "FALSE_ANSWER"
            )


        # ----------------------------------------------
        # Incomplete generation
        # ----------------------------------------------

        completeness = result.get(
            "completeness_score"
        )


        if (
            answerable
            and
            completeness is not None
            and
            completeness < 1.0
        ):

            failure_types.append(
                "INCOMPLETE_GENERATION"
            )


        # ----------------------------------------------
        # Citation ownership / coverage
        # ----------------------------------------------

        citation_coverage = result.get(
            "citation_coverage"
        )

        faithfulness = result.get(
            "faithfulness_score"
        )


        if (
            answerable
            and
            citation_coverage is not None
            and
            faithfulness is not None
            and
            citation_coverage < 0.5
            and
            faithfulness >= 0.8
        ):

            failure_types.append(
                "CITATION_COVERAGE_FAILURE"
            )


        return FailureClassification(
            case_id=result["case_id"],
            failure_types=failure_types,
        )