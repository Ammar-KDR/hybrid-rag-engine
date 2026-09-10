import re

from dataclasses import dataclass
from sentence_transformers import CrossEncoder
from sentence_transformers import (
    SentenceTransformer,
)
import numpy as np

SEMANTIC_MATCH_THRESHOLD = 0.70
LEXICAL_MATCH_THRESHOLD = 0.60


@dataclass(frozen=True)
class RequiredFactResult:

    fact: str
    matched: bool

    lexical_score: float
    semantic_score: float

    matched_by: str | None


@dataclass(frozen=True)
class GoldenAnswerEvaluation:

    total_facts: int
    covered_facts: int
    missing_facts: int

    completeness_score: float | None

    fact_results: list[RequiredFactResult]


class GoldenAnswerEvaluator:

    def __init__(
        self,
        model_name: str = (
            "cross-encoder/"
            "nli-deberta-v3-small"
        ),
    ):

        self.model = CrossEncoder(
            model_name
        )


    def evaluate(
        self,
        case,
        answer: str,
        claims=None,
    ) -> GoldenAnswerEvaluation:

        results = []

        normalized_answer = (
            self._normalize_text(
                answer
            )
        )

        answer_units = (
            self._split_answer(
                normalized_answer
            )
        )


        if claims:

            for claim in claims:

                claim_text = (
                    self._normalize_text(
                        claim.text
                    )
                )

                if claim_text:
                    answer_units.append(
                        claim_text
                    )


        for fact in case.required_facts:

            if not fact.required:
                continue


            fact_text = fact.description


            (
                matched,
                lexical_score,
                semantic_score,
                matched_by,
            ) = self._fact_matches(
                fact_text,
                normalized_answer,
                answer_units,
            )


            results.append(
                RequiredFactResult(
                    fact=fact_text,
                    matched=matched,
                    lexical_score=(
                        lexical_score
                    ),
                    semantic_score=(
                        semantic_score
                    ),
                    matched_by=matched_by,
                )
            )


        total = len(
            results
        )


        covered = sum(
            1
            for result in results
            if result.matched
        )


        missing = (
            total
            -
            covered
        )


        if total == 0:

            completeness_score = None

        else:

            completeness_score = (
                covered
                /
                total
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
        answer_units,
    ):

        normalized_fact = (
            self._normalize_text(
                fact
            )
        )


        # --------------------------------------------------
        # 1. Lexical similarity
        # --------------------------------------------------

        lexical_score = (
            self._lexical_score(
                normalized_fact,
                answer,
            )
        )


        if (
            lexical_score
            >=
            LEXICAL_MATCH_THRESHOLD
        ):

            return (
                True,
                lexical_score,
                0.0,
                "lexical",
            )


        # --------------------------------------------------
        # 2. Semantic similarity
        # --------------------------------------------------

        semantic_score = (
            self._semantic_score(
                normalized_fact,
                answer_units,
            )
        )


        if (
            semantic_score
            >=
            SEMANTIC_MATCH_THRESHOLD
        ):

            return (
                True,
                lexical_score,
                semantic_score,
                "semantic",
            )


        return (
            False,
            lexical_score,
            semantic_score,
            None,
        )


    def _lexical_score(
        self,
        fact,
        answer,
    ) -> float:

        fact_words = [
            word
            for word in fact.split()
            if len(word) > 3
        ]


        if not fact_words:
            return 0.0


        matched_words = sum(
            1
            for word in fact_words
            if word in answer
        )


        return (
            matched_words
            /
            len(fact_words)
        )


    def _semantic_score(
        self,
        fact,
        answer_units,
    ) -> float:

        if not fact:
            return 0.0

        if not answer_units:
            return 0.0


        pairs = [
            (
                answer_unit,
                fact,
            )
            for answer_unit
            in answer_units
        ]


        scores = self.model.predict(
            pairs,
        )


        probabilities = (
            np.exp(scores)
            /
            np.exp(scores).sum(
                axis=1,
                keepdims=True,
            )
        )


        entailment_scores = (
            probabilities[:, 1]
        )


        return float(
            entailment_scores.max()
        )


    def _split_answer(
        self,
        answer,
    ) -> list[str]:

        if not answer:
            return []


        # Keep the entire answer as one comparison
        # unit as well as individual sentences.
        units = [
            answer
        ]


        sentences = re.split(
            r"(?<=[.!?])\s+",
            answer,
        )


        for sentence in sentences:

            sentence = sentence.strip()

            if sentence:
                units.append(
                    sentence
                )


        return units


    def _normalize_text(
        self,
        text,
    ) -> str:

        if not text:
            return ""


        text = str(
            text
        )


        # Remove numeric RAG citations.
        text = re.sub(
            r"\[\d+\]",
            "",
            text,
        )


        # Remove markdown code markers.
        text = text.replace(
            "`",
            "",
        )


        # Normalize whitespace.
        text = " ".join(
            text
            .lower()
            .split()
        )


        return text.strip()