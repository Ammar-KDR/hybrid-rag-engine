from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CaseEvaluationResult:

    case_id: str
    primary_category: str
    difficulty: str

    expected_answerable: bool

    decision: str
    should_abstain: bool

    candidate_source_recall: float | None
    candidate_evidence_recall: float | None
    candidate_hit: bool | None
    candidate_mrr: float | None

    final_source_recall: float | None
    final_evidence_recall: float | None
    final_hit: bool | None
    final_mrr: float | None

    completeness_score: float | None
    covered_facts: int
    total_required_facts: int
    correctness_score: float | None
    correct_claims: int
    partially_correct_claims: int
    incorrect_claims: int
    correctness_results: list[dict[str, Any]]
    fact_results: list[dict[str, Any]]

    faithfulness_score: float | None

    citation_precision: float | None
    citation_coverage: float | None

    total_latency_ms: float
    verification_latency_ms: float


    def to_dict(self) -> dict[str, Any]:

        return asdict(self)