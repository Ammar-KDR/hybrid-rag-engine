from dataclasses import dataclass


@dataclass(frozen=True)
class RequiredFactResult:

    fact: str
    matched: bool


@dataclass(frozen=True)
class GoldenAnswerEvaluation:

    total_facts: int
    covered_facts: int
    missing_facts: int

    completeness_score: float | None

    fact_results: list[RequiredFactResult]



class GoldenAnswerEvaluator:


    def evaluate(
        self,
        case,
        answer: str,
    ) -> GoldenAnswerEvaluation:


        results = []


        normalized_answer = (
            self._normalize_text(
                answer
            )
        )


        for fact in case.required_facts:


            if not fact.required:
                continue

            fact_text = fact.description


            matched = (
                self._fact_matches(
                    fact_text,
                    normalized_answer,
                )
            )


            results.append(
                RequiredFactResult(
                    fact=fact_text,
                    matched=matched,
                )
            )


        total = len(results)


        covered = sum(
            1
            for result in results
            if result.matched
        )


        missing = (
            total - covered
        )


        if total == 0:

            completeness_score = None

        else:

            completeness_score = (
                covered / total
            )


        return GoldenAnswerEvaluation(

            total_facts=total,

            covered_facts=covered,

            missing_facts=missing,

            completeness_score=(
                completeness_score
            ),

            fact_results=results,
        )



    def _fact_matches(
        self,
        fact,
        answer,
    ) -> bool:


        fact = self._normalize_text(
            fact
        )


        # baseline:
        # exact semantic phrases only

        keywords = [
            word
            for word in fact.split()
            if len(word) > 4
        ]


        if not keywords:
            return False


        matched = sum(
            1
            for keyword in keywords
            if keyword in answer
        )


        return (
            matched
            /
            len(keywords)
            >= 0.5
        )



    def _normalize_text(
        self,
        text,
    ) -> str:

        return (
            text
            .lower()
            .replace(
                "`",
                "",
            )
            .strip()
        )