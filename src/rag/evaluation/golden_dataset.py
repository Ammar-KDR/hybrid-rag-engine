import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RequiredFact:
    id: str
    description: str
    required: bool
    supported_by: list[str]


@dataclass
class ExpectedSource:
    document: str
    section: str


@dataclass
class EvidenceSpan:
    id:str
    document: str
    section: str
    text: str


@dataclass
class GoldenCase:
    id: str

    primary_category: str
    tags: list[str]
    difficulty: str

    question: str

    answerable: bool
    answerability_type: str

    reference_answer: str | None

    required_facts: list[RequiredFact]
    expected_sources: list[ExpectedSource]
    evidence_spans: list[EvidenceSpan]

    acceptable_answer_paths: list[str]

    evaluation_method: str

    notes: str


def load_golden_dataset(
    path: str | Path,
) -> list[GoldenCase]:

    path = Path(path)

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw_cases = json.load(file)

    cases = []

    for item in raw_cases:

        required_facts = [
            RequiredFact(**fact)
            for fact in item["required_facts"]
        ]

        expected_sources = [
            ExpectedSource(**source)
            for source in item["expected_sources"]
        ]

        evidence_spans = [
            EvidenceSpan(**span)
            for span in item["evidence_spans"]
        ]

        case = GoldenCase(
            id=item["id"],

            primary_category=item["primary_category"],
            tags=item["tags"],
            difficulty=item["difficulty"],

            question=item["question"],

            answerable=item["answerable"],
            answerability_type=item["answerability_type"],

            reference_answer=item["reference_answer"],

            required_facts=required_facts,
            expected_sources=expected_sources,
            evidence_spans=evidence_spans,

            acceptable_answer_paths=item[
                "acceptable_answer_paths"
            ],

            evaluation_method=item["evaluation_method"],

            notes=item["notes"],
        )

        cases.append(case)

    validate_golden_dataset(cases)

    return cases

def validate_golden_dataset(
    cases: list[GoldenCase],
) -> None:

    if not cases:
        raise ValueError(
            "golden dataset cannot be empty"
        )


    # --------------------------------------------------
    # Unique IDs
    # --------------------------------------------------

    ids = [
        case.id
        for case in cases
    ]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "golden dataset contains duplicate case IDs"
        )


    # --------------------------------------------------
    # Validate individual cases
    # --------------------------------------------------

    for case in cases:

        if not case.question.strip():
            raise ValueError(
                f"{case.id}: question cannot be empty"
            )


        if case.answerable:

            if not case.reference_answer:
                raise ValueError(
                    f"{case.id}: answerable case "
                    "requires reference_answer"
                )

            if not case.required_facts:
                raise ValueError(
                    f"{case.id}: answerable case "
                    "requires required_facts"
                )

            if not case.evidence_spans:
                raise ValueError(
                    f"{case.id}: answerable case "
                    "requires evidence_spans"
                )


        if not case.answerable:

            if case.answerability_type not in {
                "unanswerable_clear",
                "unanswerable_weak_evidence",
            }:
                raise ValueError(
                    f"{case.id}: invalid "
                    "unanswerable answerability_type"
                )