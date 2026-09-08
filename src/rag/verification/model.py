from dataclasses import dataclass
from enum import Enum
from rag.generation.model import GeneratedAnswer

@dataclass
class Claim:
    text: str
    citations: list[int]


@dataclass
class ClaimExtractionResult:
    claims: list[Claim]
    invalid_references: list[int]

    model: str

    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None

    latency_ms: float

class SupportVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


@dataclass
class CitationVerification:
    claim_text: str
    reference: int
    verdict: SupportVerdict
    explanation: str

@dataclass
class CitationVerificationResult:
    verifications: list[CitationVerification]
    uncited_claims: list[Claim]
    unresolved_references: list[int]


@dataclass
class CitationMetrics:
    citation_precision: float | None
    citation_coverage: float | None

    total_verifications: int
    supported_verifications: int
    partially_supported_verifications: int
    unsupported_verifications: int
    contradicted_verifications: int

    total_claims: int
    adequately_cited_claims: int
    uncited_claims: int

@dataclass
class ClaimFaithfulness:
    claim_text: str
    verdict: SupportVerdict
    explanation: str

@dataclass
class FaithfulnessSummary:
    claim_results: list[ClaimFaithfulness]

    total_claims: int
    supported_claims: int
    partially_supported_claims: int
    unsupported_claims: int
    contradicted_claims: int




@dataclass
class AbstentionSignals:
    total_claims: int

    supported_claims: int
    partially_supported_claims: int
    unsupported_claims: int
    contradicted_claims: int

    uncited_claims: int
    unresolved_references: int

    citation_precision: float | None
    citation_coverage: float | None


@dataclass
class AbstentionDecision:
    should_abstain: bool
    reasons: list[str]
    signals: AbstentionSignals

@dataclass
class VerifiedAnswer:
    generated_answer: GeneratedAnswer

    claims: ClaimExtractionResult

    citation_verification: CitationVerificationResult
    citation_metrics: CitationMetrics

    faithfulness: FaithfulnessSummary
    final_answer: str

    abstention: AbstentionDecision
    verification_latency_ms:float