import json
from pathlib import Path
from statistics import mean


class BenchmarkAggregator: 

    def load_results(
        self,
        path: str,
    ) -> list[dict]:

        path = Path(path)

        results = []

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                results.append(
                    json.loads(line)
                )

        return results


    def aggregate(
        self,
        results: list[dict],
    ) -> dict:

        answerable = [
            result
            for result in results
            if result["expected_answerable"]
        ]

        unanswerable = [
            result
            for result in results
            if not result["expected_answerable"]
        ]


        # --------------------------------------------------
        # Abstention behavior
        # --------------------------------------------------

        answerable_answered = sum(
            1
            for result in answerable
            if not result["should_abstain"]
        )

        answerable_abstained = sum(
            1
            for result in answerable
            if result["should_abstain"]
        )

        unanswerable_answered = sum(
            1
            for result in unanswerable
            if not result["should_abstain"]
        )

        unanswerable_abstained = sum(
            1
            for result in unanswerable
            if result["should_abstain"]
        )


        total_correct_behavior = (
            answerable_answered
            +
            unanswerable_abstained
        )


        behavior_accuracy = (
            total_correct_behavior
            /
            len(results)
            if results
            else None
        )


        false_abstention_rate = (
            answerable_abstained
            /
            len(answerable)
            if answerable
            else None
        )


        false_answer_rate = (
            unanswerable_answered
            /
            len(unanswerable)
            if unanswerable
            else None
        )


        # --------------------------------------------------
        # Retrieval metrics
        #
        # Only answerable cases belong in retrieval recall.
        # --------------------------------------------------

        candidate_hit_rate = (
            self._mean_boolean(
                answerable,
                "candidate_hit",
            )
        )

        final_hit_rate = (
            self._mean_boolean(
                answerable,
                "final_hit",
            )
        )


        candidate_source_recall = (
            self._mean_value(
                answerable,
                "candidate_source_recall",
            )
        )

        candidate_evidence_recall = (
            self._mean_value(
                answerable,
                "candidate_evidence_recall",
            )
        )

        candidate_mrr = (
            self._mean_value(
                answerable,
                "candidate_mrr",
            )
        )


        final_source_recall = (
            self._mean_value(
                answerable,
                "final_source_recall",
            )
        )

        final_evidence_recall = (
            self._mean_value(
                answerable,
                "final_evidence_recall",
            )
        )

        final_mrr = (
            self._mean_value(
                answerable,
                "final_mrr",
            )
        )


        # --------------------------------------------------
        # Completeness
        # --------------------------------------------------

        average_completeness = (
            self._mean_value(
                answerable,
                "completeness_score",
            )
        )


        total_required_facts = sum(
            result["total_required_facts"]
            for result in answerable
        )

        total_covered_facts = sum(
            result["covered_facts"]
            for result in answerable
        )


        required_fact_coverage = (
            total_covered_facts
            /
            total_required_facts
            if total_required_facts > 0
            else None
        )


        fully_complete_answers = sum(
            1
            for result in answerable
            if (
                result["completeness_score"]
                ==
                1.0
            )
        )


        fully_complete_rate = (
            fully_complete_answers
            /
            len(answerable)
            if answerable
            else None
        )


        # --------------------------------------------------
        # Faithfulness / citations
        # --------------------------------------------------

        average_faithfulness = (
            self._mean_value(
                results,
                "faithfulness_score",
            )
        )

        average_citation_precision = (
            self._mean_value(
                results,
                "citation_precision",
            )
        )

        average_citation_coverage = (
            self._mean_value(
                results,
                "citation_coverage",
            )
        )


        # --------------------------------------------------
        # Latency
        # --------------------------------------------------

        average_latency_ms = (
            self._mean_value(
                results,
                "total_latency_ms",
            )
        )

        average_verification_latency_ms = (
            self._mean_value(
                results,
                "verification_latency_ms",
            )
        )


        if (
            average_latency_ms
            and
            average_verification_latency_ms
        ):

            verification_latency_share = (
                average_verification_latency_ms
                /
                average_latency_ms
            )

        else:

            verification_latency_share = None


        # --------------------------------------------------
        # Failure IDs
        # --------------------------------------------------

        false_abstention_case_ids = [
            result["case_id"]
            for result in answerable
            if result["should_abstain"]
        ]


        false_answer_case_ids = [
            result["case_id"]
            for result in unanswerable
            if not result["should_abstain"]
        ]


        candidate_miss_case_ids = [
            result["case_id"]
            for result in answerable
            if result["candidate_hit"] is False
        ]


        final_miss_case_ids = [
            result["case_id"]
            for result in answerable
            if result["final_hit"] is False
        ]


        incomplete_case_ids = [
            result["case_id"]
            for result in answerable
            if (
                result["completeness_score"]
                is not None
                and
                result["completeness_score"]
                < 1.0
            )
        ]
                # --------------------------------------------------
        # Group breakdowns
        # --------------------------------------------------

        by_category = (
            self._group_results(
                results=results,
                field="primary_category",
            )
        )

        by_difficulty = (
            self._group_results(
                results=results,
                field="difficulty",
            )
        )

        by_answerability = {
            "answerable": (
                self._aggregate_group(
                    answerable
                )
            ),
            "unanswerable": (
                self._aggregate_group(
                    unanswerable
                )
            ),
        }

        return {

            "total_cases": len(results),

            "answerable_cases": len(answerable),
            "unanswerable_cases": len(unanswerable),

            "abstention": {
                "answerable_answered": (
                    answerable_answered
                ),
                "answerable_abstained": (
                    answerable_abstained
                ),
                "unanswerable_answered": (
                    unanswerable_answered
                ),
                "unanswerable_abstained": (
                    unanswerable_abstained
                ),
                "behavior_accuracy": (
                    behavior_accuracy
                ),
                "false_abstention_rate": (
                    false_abstention_rate
                ),
                "false_answer_rate": (
                    false_answer_rate
                ),
            },

            "retrieval": {
                "candidate_hit_rate": (
                    candidate_hit_rate
                ),
                "candidate_source_recall": (
                    candidate_source_recall
                ),
                "candidate_evidence_recall": (
                    candidate_evidence_recall
                ),
                "candidate_mrr": (
                    candidate_mrr
                ),

                "final_hit_rate": (
                    final_hit_rate
                ),
                "final_source_recall": (
                    final_source_recall
                ),
                "final_evidence_recall": (
                    final_evidence_recall
                ),
                "final_mrr": (
                    final_mrr
                ),
            },

            "completeness": {
                "average_completeness": (
                    average_completeness
                ),
                "covered_required_facts": (
                    total_covered_facts
                ),
                "total_required_facts": (
                    total_required_facts
                ),
                "required_fact_coverage": (
                    required_fact_coverage
                ),
                "fully_complete_answers": (
                    fully_complete_answers
                ),
                "fully_complete_rate": (
                    fully_complete_rate
                ),
            },
            "correctness": self.aggregate_correctness(
                            results
                            ),

            "verification": {
                "average_faithfulness": (
                    average_faithfulness
                ),
                "average_citation_precision": (
                    average_citation_precision
                ),
                "average_citation_coverage": (
                    average_citation_coverage
                ),
            },

            "latency": {
                "average_total_ms": (
                    average_latency_ms
                ),
                "average_verification_ms": (
                    average_verification_latency_ms
                ),
                "verification_share": (
                    verification_latency_share
                ),
            },

            "failures": {
                "false_abstentions": (
                    false_abstention_case_ids
                ),
                "false_answers": (
                    false_answer_case_ids
                ),
                "candidate_misses": (
                    candidate_miss_case_ids
                ),
                "final_misses": (
                    final_miss_case_ids
                ),
                "incomplete_answers": (
                    incomplete_case_ids
                ),
            },
                        "breakdowns": {

                "by_category": (
                    by_category
                ),

                "by_difficulty": (
                    by_difficulty
                ),

                "by_answerability": (
                    by_answerability
                ),
            },
        }


    def aggregate_correctness(
        self,
        results: list[dict],
    ) -> dict:

        scored_results = [
            result
            for result in results
            if (
                result.get("expected_answerable")
                and result.get("correctness_score")
                is not None
            )
        ]

        if not scored_results:

            return {
                "average_correctness": None,
                "fully_correct_answers": 0,
                "fully_correct_rate": None,
                "total_incorrect_claims": 0,
            }


        average_correctness = (
            sum(
                result["correctness_score"]
                for result in scored_results
            )
            /
            len(scored_results)
        )


        fully_correct_answers = sum(
            1
            for result in scored_results
            if (
                result.get(
                    "partially_correct_claims",
                    0,
                )
                == 0
                and result.get(
                    "incorrect_claims",
                    0,
                )
                == 0
            )
        )


        fully_correct_rate = (
            fully_correct_answers
            /
            len(scored_results)
        )


        total_incorrect_claims = sum(
            result.get(
                "incorrect_claims",
                0,
            )
            for result in scored_results
        )


        return {
            "average_correctness": (
                average_correctness
            ),
            "fully_correct_answers": (
                fully_correct_answers
            ),
            "fully_correct_rate": (
                fully_correct_rate
            ),
            "total_incorrect_claims": (
                total_incorrect_claims
            ),
        }
    def _mean_value(
        self,
        results,
        field,
    ) -> float | None:

        values = [
            result[field]
            for result in results
            if result[field] is not None
        ]

        if not values:
            return None

        return mean(values)


    def _mean_boolean(
        self,
        results,
        field,
    ) -> float | None:

        values = [
            result[field]
            for result in results
            if result[field] is not None
        ]

        if not values:
            return None

        return (
            sum(
                1
                for value in values
                if value
            )
            /
            len(values)
        )

    def _group_results(
        self,
        results,
        field,
    ) -> dict:

        groups = {}


        for result in results:

            key = result.get(
                field
            )


            if key not in groups:

                groups[key] = []


            groups[key].append(
                result
            )


        return {
            key: self._aggregate_group(
                group_results
            )
            for key, group_results
            in groups.items()
        }


    def _aggregate_group(
        self,
        results,
    ) -> dict:

        if not results:

            return {}


        answerable = [
            result
            for result in results
            if result[
                "expected_answerable"
            ]
        ]


        unanswerable = [
            result
            for result in results
            if not result[
                "expected_answerable"
            ]
        ]


        # --------------------------------------------------
        # Abstention behavior
        # --------------------------------------------------

        correct_behavior = sum(
            1
            for result in results
            if (
                (
                    result[
                        "expected_answerable"
                    ]
                    and
                    not result[
                        "should_abstain"
                    ]
                )
                or
                (
                    not result[
                        "expected_answerable"
                    ]
                    and
                    result[
                        "should_abstain"
                    ]
                )
            )
        )


        behavior_accuracy = (
            correct_behavior
            /
            len(results)
        )


        false_abstentions = sum(
            1
            for result in answerable
            if result[
                "should_abstain"
            ]
        )


        false_answers = sum(
            1
            for result in unanswerable
            if not result[
                "should_abstain"
            ]
        )


        false_abstention_rate = (
            false_abstentions
            /
            len(answerable)
            if answerable
            else None
        )


        false_answer_rate = (
            false_answers
            /
            len(unanswerable)
            if unanswerable
            else None
        )


        # --------------------------------------------------
        # Decisions
        # --------------------------------------------------

        decision_counts = {}


        for result in results:

            decision = result[
                "decision"
            ]

            decision_counts[
                decision
            ] = (
                decision_counts.get(
                    decision,
                    0,
                )
                +
                1
            )


        # --------------------------------------------------
        # Completeness
        # --------------------------------------------------

        total_required_facts = sum(
            result[
                "total_required_facts"
            ]
            for result in answerable
        )


        covered_required_facts = sum(
            result[
                "covered_facts"
            ]
            for result in answerable
        )


        if total_required_facts > 0:

            required_fact_coverage = (
                covered_required_facts
                /
                total_required_facts
            )

        else:

            required_fact_coverage = None

        correctness_scores = [
            result.correctness_score
            for result in results
            if result.correctness_score is not None
        ]


        average_correctness = (
            sum(correctness_scores)
            / len(correctness_scores)
            if correctness_scores
            else None
        )


        correctness_cases = [
            result
            for result in results
            if result.correctness_score is not None
        ]


        fully_correct_answers = sum(
            1
            for result in correctness_cases
            if result.incorrect_claims == 0
            and result.partially_correct_claims == 0
        )


        fully_correct_rate = (
            fully_correct_answers
            / len(correctness_cases)
            if correctness_cases
            else None
        )


        total_incorrect_claims = sum(
            result.incorrect_claims
            for result in correctness_cases
        )

        # --------------------------------------------------
        # Result
        # --------------------------------------------------

        return {

            "cases": len(results),

            "answerable_cases": (
                len(answerable)
            ),

            "unanswerable_cases": (
                len(unanswerable)
            ),

            "behavior_accuracy": (
                behavior_accuracy
            ),

            "false_abstention_rate": (
                false_abstention_rate
            ),

            "false_answer_rate": (
                false_answer_rate
            ),

            "candidate_hit_rate": (
                self._mean_boolean(
                    answerable,
                    "candidate_hit",
                )
            ),

            "candidate_evidence_recall": (
                self._mean_value(
                    answerable,
                    "candidate_evidence_recall",
                )
            ),

            "final_hit_rate": (
                self._mean_boolean(
                    answerable,
                    "final_hit",
                )
            ),

            "final_evidence_recall": (
                self._mean_value(
                    answerable,
                    "final_evidence_recall",
                )
            ),

            "average_completeness": (
                self._mean_value(
                    answerable,
                    "completeness_score",
                )
            ),

            "required_fact_coverage": (
                required_fact_coverage
            ),

            "average_faithfulness": (
                self._mean_value(
                    results,
                    "faithfulness_score",
                )
            ),

            "average_citation_precision": (
                self._mean_value(
                    results,
                    "citation_precision",
                )
            ),

            "average_citation_coverage": (
                self._mean_value(
                    results,
                    "citation_coverage",
                )
            ),

            "average_latency_ms": (
                self._mean_value(
                    results,
                    "total_latency_ms",
                )
            ),

            "decisions": (
                decision_counts
            ),
            "correctness": {
                "average_correctness": average_correctness,
                "fully_correct_answers": fully_correct_answers,
                "fully_correct_rate": fully_correct_rate,
                "total_incorrect_claims": total_incorrect_claims,
            },
        }