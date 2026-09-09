import time

from .model import VerifiedAnswer,CitationVerificationResult

class AnswerVerificationPipeline:

    ABSTENTION_MESSAGE = (
        "The available evidence is insufficient "
        "to answer this question."
    )

    def __init__(
        self,
        claim_extractor,
        citation_runner,
        metrics_calculator,
        faithfulness_evaluator,
        abstention_policy,
    ):
        self.claim_extractor = claim_extractor
        self.citation_runner = citation_runner
        self.metrics_calculator = metrics_calculator
        self.faithfulness_evaluator = faithfulness_evaluator
        self.abstention_policy = abstention_policy

    def verify(
        self,
        generated_answer,
    ) -> VerifiedAnswer:

        start = time.perf_counter()

        # -----------------------------------------------------
        # 1. Extract factual claims
        # -----------------------------------------------------

        claim_extraction = self.claim_extractor.extract(
            generated_answer.answer
        )

        claims = claim_extraction.claims

        # -----------------------------------------------------
        # 2. Build citation -> evidence mapping
        # -----------------------------------------------------

        evidence_by_reference = {
            block.reference: block.text
            for block in generated_answer.evidence
        }

        # -----------------------------------------------------
        # 3. Verify attached citations
        # -----------------------------------------------------

        citation_verification = self.citation_runner.run(
            claims=claims,
            evidence_by_reference=evidence_by_reference,
        )

        # -----------------------------------------------------
        # 4. Preserve unresolved references already detected
        #    by Day 8
        # -----------------------------------------------------

        unresolved_references = list(
            dict.fromkeys(
                generated_answer.unresolved_references
                + citation_verification.unresolved_references
            )
        )

        citation_verification = CitationVerificationResult(
            verifications=citation_verification.verifications,
            uncited_claims=citation_verification.uncited_claims,
            unresolved_references=unresolved_references,
        )

        # -----------------------------------------------------
        # 5. Calculate citation quality metrics
        # -----------------------------------------------------

        citation_metrics = self.metrics_calculator.calculate(
            claims=claims,
            verification_result=citation_verification,
        )

        # -----------------------------------------------------
        # 6. Build ALL evidence supplied to generation
        # -----------------------------------------------------

        evidence_text = "\n\n".join(
            (
                f"[{block.reference}]\n"
                f"{block.text}"
            )
            for block in generated_answer.evidence
        )

        # -----------------------------------------------------
        # 7. Evaluate claim faithfulness against ALL evidence
        # -----------------------------------------------------

        faithfulness = self.faithfulness_evaluator.evaluate(
            question=generated_answer.question,
            claims=claims,
            evidence_text=evidence_text,
        )

        # -----------------------------------------------------
        # 8. Decide whether answer should be returned
        # -----------------------------------------------------

        abstention = self.abstention_policy.decide(
            faithfulness=faithfulness,
            citation_verification=citation_verification,
            citation_metrics=citation_metrics,
        )

        # -----------------------------------------------------
        # 9. Produce final externally returned answer
        # -----------------------------------------------------

        if abstention.should_abstain:
            final_answer = self.ABSTENTION_MESSAGE
        else:
            final_answer = generated_answer.answer

        verification_latency_ms = (
            time.perf_counter() - start
        ) * 1000

        return VerifiedAnswer(
            generated_answer=generated_answer,
            claims=claim_extraction,
            citation_verification=citation_verification,
            citation_metrics=citation_metrics,
            faithfulness=faithfulness,
            abstention=abstention,
            final_answer=final_answer,
            verification_latency_ms=verification_latency_ms,
        )
