from rag.evaluation.golden_dataset import (
    load_golden_dataset,
)
from rag.evaluation.retrieval_evidence_evaluator import (
    RetrievalEvidenceEvaluator,
)
from rag.factory import create_rag_pipeline
from dataclasses import asdict
from rag.evaluation.golden_answer_eval import (
    GoldenAnswerEvaluator,
)
from rag.evaluation.case_evaluation_result import (
    CaseEvaluationResult,
)

from rag.evaluation.evaluation_result_store import (
    EvaluationResultStore,
)
from rag.evaluation.gold_correctness_eval import GoldenCorrectnessEvaluation , LMStudioCorrectnessJudge ,GoldenCorrectnessEvaluator
TEXT_PREVIEW_LENGTH = 500
FAITHFULNESS_FAILURE_THRESHOLD = 0.7

def print_candidate(
    index,
    chunk,
):
    metadata = chunk.metadata or {}

    retrieval = metadata.get(
        "retrieval",
        {},
    )

    sources = retrieval.get(
        "sources",
        {},
    )

    dense = sources.get(
        "dense"
    )

    bm25 = sources.get(
        "bm25"
    )

    heading_path = metadata.get(
        "heading_path",
        [],
    )

    if heading_path:
        section = " > ".join(
            heading_path
        )
    else:
        section = metadata.get(
            "heading",
            "N/A",
        )

    text_preview = chunk.text[
        :TEXT_PREVIEW_LENGTH
    ]

    if len(chunk.text) > TEXT_PREVIEW_LENGTH:
        text_preview += "..."

    print("-" * 70)
    print(
        f"CANDIDATE #{index}"
    )
    print("-" * 70)

    print(
        "Chunk ID:",
        chunk.chunk_id,
    )

    print(
        "Source:",
        metadata.get(
            "source",
            "N/A",
        ),
    )

    print(
        "Section:",
        section,
    )

    print()

    print(
        "Hybrid rank:",
        chunk.rank,
    )

    print(
        "RRF score:",
        round(
            chunk.score,
            6,
        ),
    )

    print()

    if dense:
        print(
            "Dense:",
            f"rank={dense.get('rank')},",
            f"score={round(dense.get('score'), 6)}",
        )
    else:
        print(
            "Dense: not retrieved"
        )

    if bm25:
        print(
            "BM25:",
            f"rank={bm25.get('rank')},",
            f"score={round(bm25.get('score'), 6)}",
        )
    else:
        print(
            "BM25: not retrieved"
        )

    print()
    print("TEXT PREVIEW:")
    print(text_preview)


def print_reranked_chunk(
    index,
    chunk,
):
    metadata = chunk.metadata or {}

    heading_path = metadata.get(
        "heading_path",
        [],
    )

    if heading_path:
        section = " > ".join(
            heading_path
        )
    else:
        section = metadata.get(
            "heading",
            "N/A",
        )

    print("-" * 70)
    print(
        f"FINAL CHUNK #{index}"
    )
    print("-" * 70)

    print(
        "Chunk ID:",
        chunk.chunk_id,
    )

    print(
        "Source:",
        metadata.get(
            "source",
            "N/A",
        ),
    )

    print(
        "Section:",
        section,
    )

    print()

    print("Retrieval:")
    print(
        "  Rank:",
        chunk.retrieval_rank,
    )
    print(
        "  Score:",
        round(
            chunk.retrieval_score,
            6,
        ),
    )

    print()

    print("Cross Encoder:")
    print(
        "  Rank:",
        chunk.reranked_rank,
    )
    print(
        "  Score:",
        round(
            chunk.reranker_score,
            6,
        ),
    )

    print()

    print("Final Fusion:")
    print(
        "  Rank:",
        chunk.final_rank,
    )
    print(
        "  Score:",
        round(
            chunk.final_score,
            6,
        ),
    )

    print()
    print("FULL TEXT:")
    print(chunk.text)


def main():

    # --------------------------------------------------
    # 1. Load golden dataset
    # --------------------------------------------------

    cases = load_golden_dataset(
        "data/evaluation/day10_golden_rag_dataset_v1.json"
    )

    
    case_ids = [
    case.id
    for case in cases
]

    case_lookup = {
        case.id: case
        for case in cases
    }


    # --------------------------------------------------
    # 2. Build full RAG pipeline
    # --------------------------------------------------

    pipeline = create_rag_pipeline()
    retrieval_evaluator = (
    RetrievalEvidenceEvaluator()
)
    golden_answer_evaluator = (
        GoldenAnswerEvaluator()
    )
    correctness_judge = (
    LMStudioCorrectnessJudge()
)

    golden_correctness_evaluator = (
        GoldenCorrectnessEvaluator(
            judge=correctness_judge
        )
    )


   

    results = []
    result_store = (
    EvaluationResultStore(
        path="data/evaluation/day10_structure_corr_v1.jsonl"
    )
)

    completed_case_ids = (
        result_store.load_completed_case_ids()
    )
    for case_id in case_ids:

        case = case_lookup[case_id]

        if case.id in completed_case_ids:

            print(
                f"Skipping completed case: {case.id}"
            )

            continue


        result = pipeline.run(
            case.question
        )
        retrieval_evaluation = (
        retrieval_evaluator.evaluate(
        case=case,
        candidates=result.candidates,
        reranked_chunks=(
            result.reranked_chunks[:5]
        ),
    )
)
        golden_answer_evaluation = (
            golden_answer_evaluator.evaluate(
                case=case,
                answer=(
                    result
                    .answer
                    .answer
                ),

                claims=(
                    result
                    .verified_answer
                    .claims
                    .claims
                ),
            )
        )
        golden_correctness_evaluation = (
            golden_correctness_evaluator.evaluate(
                case=case,
                claims=(
                    result
                    .verified_answer
                    .claims
                    .claims
                ),
            )
        )
        golden_correctness_evaluation = (
        golden_correctness_evaluator.evaluate(
            case=case,
            claims=result.verified_answer.claims.claims,
        )
    )
        case_evaluation_result = (
            CaseEvaluationResult(

                case_id=case.id,

                primary_category=(
                    case.primary_category
                ),

                difficulty=(
                    case.difficulty
                ),

                expected_answerable=(
                    case.answerable
                ),

                decision=(
                    result
                    .verified_answer
                    .abstention
                    .decision
                    .value
                ),

                should_abstain=(
                    result
                    .verified_answer
                    .abstention
                    .should_abstain
                ),

                candidate_source_recall=(
                    retrieval_evaluation
                    .candidate
                    .source_recall
                ),

                candidate_evidence_recall=(
                    retrieval_evaluation
                    .candidate
                    .evidence_span_recall
                ),

                candidate_hit=(
                    retrieval_evaluation
                    .candidate
                    .hit
                ),

                candidate_mrr=(
                    retrieval_evaluation
                    .candidate
                    .mrr
                ),

                final_source_recall=(
                    retrieval_evaluation
                    .final
                    .source_recall
                ),

                final_evidence_recall=(
                    retrieval_evaluation
                    .final
                    .evidence_span_recall
                ),

                final_hit=(
                    retrieval_evaluation
                    .final
                    .hit
                ),

                final_mrr=(
                    retrieval_evaluation
                    .final
                    .mrr
                ),

                completeness_score=(
                    golden_answer_evaluation
                    .completeness_score
                ),

                covered_facts=(
                    golden_answer_evaluation
                    .covered_facts
                ),

                total_required_facts=(
                    golden_answer_evaluation
                    .total_facts
                ),

                fact_results=[
                    {
                        "fact": fact.fact,
                        "matched": fact.matched,
                        "lexical_score": (
                            fact.lexical_score
                        ),
                        "semantic_score": (
                            fact.semantic_score
                        ),
                        "matched_by": (
                            fact.matched_by
                        ),
                    }
                    for fact in (
                        golden_answer_evaluation
                        .fact_results
                    )
                ],

                faithfulness_score=(
                    result
                    .verified_answer
                    .abstention
                    .signals
                    .faithfulness_score
                ),

                citation_precision=(
                    result
                    .verified_answer
                    .citation_metrics
                    .citation_precision
                ),

                citation_coverage=(
                    result
                    .verified_answer
                    .citation_metrics
                    .citation_coverage
                ),

                total_latency_ms=(
                    result.total_latency_ms
                ),

                verification_latency_ms=(
                    result.verification_latency_ms
                ),
                correctness_score=(
                    golden_correctness_evaluation.correctness_score
                ),

                correct_claims=(
                    golden_correctness_evaluation.correct_claims
                ),

                partially_correct_claims=(
                    golden_correctness_evaluation.partially_correct_claims
                ),

                incorrect_claims=(
                    golden_correctness_evaluation.incorrect_claims
                ),

                correctness_results=[
                    {
                        "claim": result.claim,
                        "verdict": result.verdict.value,
                        "explanation": result.explanation,
                    }
                    for result
                    in golden_correctness_evaluation.claim_results
                ],
            )
        )


        result_store.append(
            case_evaluation_result
        )


        completed_case_ids.add(
            case.id
        )
        

        print_case_summary(
            case,
            result,
            retrieval_evaluation,
            golden_answer_evaluation,
            golden_correctness_evaluation,

        )


        results.append(
        {
            "case": case.id,
            "answerable": case.answerable,
            "decision": (
                result
                .verified_answer
                .abstention
                .decision
                .value
            ),
            "faithfulness": (
                result
                .verified_answer
                .abstention
                .signals
                .faithfulness_score
            ),
            "citation_precision": (
                result
                .verified_answer
                .citation_metrics
                .citation_precision
            ),
            "citation_coverage": (
                result
                .verified_answer
                .citation_metrics
                .citation_coverage
            ),
            "latency": (
                result.total_latency_ms
            ),
        }
    )


        if is_failure_case(
            case,
            result,
        ):

            print("\n")
            print("#" * 70)
            print(
                "DETAILED FAILURE DEBUG:",
                case.id,
            )
            print("#" * 70)

            print(
                result
                .verified_answer
                .final_answer
            )

            print()

            for index, chunk in enumerate(
                result.reranked_chunks[:5],
                start=1,
            ):
                print_reranked_chunk(
                    index,
                    chunk,
                )
    print("\n")
    print("#" * 70)
    print("FINAL BENCHMARK SUMMARY")
    print("#" * 70)


    print(
        "Total cases:",
        len(results),
    )


    faithfulness_values = [
        r["faithfulness"]
        for r in results
        if r["faithfulness"] is not None
    ]


    if faithfulness_values:

        average_faithfulness = (
            sum(faithfulness_values)
            /
            len(faithfulness_values)
        )

    else:

        average_faithfulness = None


    print(
        "Average faithfulness:",
        (
            round(
                average_faithfulness,
                3,
            )
            if average_faithfulness is not None
            else "N/A"
        ),
    )


    print(
        "Average latency:",
        round(
            sum(
                r["latency"]
                for r in results
            )
            /
            len(results),
            2,
        ),
        "ms",
    )


    print()

    print(
        "Decisions:"
    )

    decisions = {}

    for result in results:

        decision = result["decision"]

        decisions[decision] = (
            decisions.get(decision, 0)
            + 1
        )


    for key, value in decisions.items():

        print(
            key,
            ":",
            value,
        )
        

def print_case_summary(
    case,
    result,
    retrieval_evaluation,
    golden_answer_evaluation,
    golden_correctness_evaluation,
):

    faithfulness = (
        result
        .verified_answer
        .faithfulness
    )

    citation_metrics = (
        result
        .verified_answer
        .citation_metrics
    )

    abstention = (
        result
        .verified_answer
        .abstention
    )


    print("=" * 70)
    print(
        "CASE:",
        case.id,
    )
    print("=" * 70)

    print(
        "Category:",
        case.primary_category,
    )

    print(
        "Expected answerable:",
        case.answerable,
    )

    print(
        "Decision:",
        abstention.decision.value,
    )

    print(
        "Should abstain:",
        abstention.should_abstain,
    )


    print()

    if abstention.signals.faithfulness_score is None:

        faithfulness_score_display = "N/A"

    else:

        faithfulness_score_display = round(
            abstention.signals.faithfulness_score,
            3,
        )


    print(
        "Faithfulness score:",
        faithfulness_score_display,
    )
    print(
        "Supported:",
        faithfulness.supported_claims,
    )

    print(
        "Partial:",
        faithfulness.partially_supported_claims,
    )

    print(
        "Unsupported:",
        faithfulness.unsupported_claims,
    )

    print(
        "Contradicted:",
        faithfulness.contradicted_claims,
    )


    print()

    print(
        "Citation precision:",
        citation_metrics.citation_precision,
    )

    print(
        "Citation coverage:",
        citation_metrics.citation_coverage,
    )


    print()

    print(
        "Latency total:",
        round(
            result.total_latency_ms,
            2,
        ),
        "ms",
    )

    print(
        "Latency verification:",
        round(
            result.verification_latency_ms,
            2,
        ),
        "ms",
    )
    print()

    print("Retrieval evaluation:")

    print(
        "Candidate source Recall@20:",
        retrieval_evaluation
        .candidate
        .source_recall,
    )

    print(
        "Candidate evidence Recall@20:",
        retrieval_evaluation
        .candidate
        .evidence_span_recall,
    )

    print(
        "Candidate Hit@20:",
        retrieval_evaluation
        .candidate
        .hit,
    )

    print(
        "Candidate MRR@20:",
        retrieval_evaluation
        .candidate
        .mrr,
    )

    print()

    print(
        "Final source Recall@5:",
        retrieval_evaluation
        .final
        .source_recall,
    )

    print(
        "Final evidence Recall@5:",
        retrieval_evaluation
        .final
        .evidence_span_recall,
    )

    print(
        "Final Hit@5:",
        retrieval_evaluation
        .final
        .hit,
    )

    print(
        "Final MRR@5:",
        retrieval_evaluation
        .final
        .mrr,
    )
    print()

    print(
        "Completeness:"
    )

    print(
        "Covered facts:",
        golden_answer_evaluation.covered_facts,
        "/",
        golden_answer_evaluation.total_facts,
    )

    print(
        "Completeness score:",
        golden_answer_evaluation.completeness_score,
)

    for fact_result in (
        golden_answer_evaluation
        .fact_results
    ):

        print(
            "-",
            fact_result.matched,
            "| lexical:",
            round(
                fact_result.lexical_score,
                3,
            ),
            "| semantic:",
            round(
                fact_result.semantic_score,
                3,
            ),
            "| by:",
            fact_result.matched_by,
            "|",
            fact_result.fact,
        )
        print()
        print("Correctness:")

        print(
            "Correctness score:",
            golden_correctness_evaluation.correctness_score,
        )

        print(
            "Correct claims:",
            golden_correctness_evaluation.correct_claims,
        )

        print(
            "Partially correct claims:",
            golden_correctness_evaluation.partially_correct_claims,
        )

        print(
            "Incorrect claims:",
            golden_correctness_evaluation.incorrect_claims,
        )

        for claim_result in (
            golden_correctness_evaluation.claim_results
        ):

            print(
                "-",
                claim_result.verdict.value,
                "|",
                claim_result.claim,
                "|",
                claim_result.explanation,
            )


def is_failure_case(
    case,
    result,
):

    decision = (
        result
        .verified_answer
        .abstention
    )

    faithfulness = (
        result
        .verified_answer
        .faithfulness
    )


    # False abstention
    if (
        case.answerable
        and decision.should_abstain
    ):
        return True


    # False acceptance
    if (
        not case.answerable
        and not decision.should_abstain
    ):
        return True


    # Low faithfulness
    if (
        decision.signals.faithfulness_score is not None
        and decision.signals.faithfulness_score
        <
        FAITHFULNESS_FAILURE_THRESHOLD
    ):
        return True


    return False
if __name__ == "__main__":
    main()