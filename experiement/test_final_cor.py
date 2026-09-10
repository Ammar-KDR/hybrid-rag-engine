import json

from pathlib import Path
from types import SimpleNamespace

from rag.evaluation.golden_dataset import (
    load_golden_dataset,
)

from rag.evaluation.gold_correctness_eval import (
    GoldenCorrectnessEvaluator,
    LMStudioCorrectnessJudge,
)


INPUT_PATH = Path(
    "data/evaluation/day10_structure_corr_v1.jsonl"
)

OUTPUT_PATH = Path(
    "data/evaluation/day10_structure_cor_v6.jsonl"
)

GOLDEN_DATASET_PATH = (
    "data/evaluation/day10_golden_rag_dataset_v1.json"
)


def load_jsonl(
    path: Path,
) -> list[dict]:

    rows = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:

                rows.append(
                    json.loads(line)
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    f"Invalid JSON on line "
                    f"{line_number} of {path}"
                ) from exc

    return rows


def extract_saved_claims(
    row: dict,
):

    correctness_results = (
        row.get(
            "correctness_results",
            [],
        )
        or []
    )

    return [
        SimpleNamespace(
            text=item["claim"]
        )
        for item in correctness_results
        if item.get("claim")
    ]


def build_correctness_results(
    evaluation,
) -> list[dict]:

    return [
        {
            "claim": item.claim,
            "verdict": item.verdict.value,
            "explanation": item.explanation,
        }
        for item in evaluation.claim_results
    ]


def main():

    # --------------------------------------------------
    # 1. Safety checks
    # --------------------------------------------------

    if not INPUT_PATH.exists():

        raise FileNotFoundError(
            f"Input JSONL not found: "
            f"{INPUT_PATH}"
        )


    if OUTPUT_PATH.exists():

        raise FileExistsError(
            f"Output already exists: "
            f"{OUTPUT_PATH}\n"
            "Delete it manually if you really "
            "want to rerun the correctness judge."
        )


    # --------------------------------------------------
    # 2. Load golden dataset
    # --------------------------------------------------

    cases = load_golden_dataset(
        GOLDEN_DATASET_PATH
    )

    case_lookup = {
        case.id: case
        for case in cases
    }


    # --------------------------------------------------
    # 3. Load previous 60-case results
    # --------------------------------------------------

    rows = load_jsonl(
        INPUT_PATH
    )


    print(
        "Loaded benchmark rows:",
        len(rows),
    )


    # --------------------------------------------------
    # 4. Build corrected judge
    # --------------------------------------------------

    judge = (
        LMStudioCorrectnessJudge()
    )

    evaluator = (
        GoldenCorrectnessEvaluator(
            judge=judge
        )
    )


    # --------------------------------------------------
    # 5. Rejudge correctness only
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    processed = 0

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for row in rows:

            case_id = row["case_id"]

            if case_id not in case_lookup:

                raise KeyError(
                    f"Golden case not found: "
                    f"{case_id}"
                )


            case = case_lookup[
                case_id
            ]


            saved_claims = (
                extract_saved_claims(
                    row
                )
            )


            print()
            print("=" * 70)

            print(
                "REJUDGING:",
                case_id,
            )

            print(
                "Answerable:",
                case.answerable,
            )

            print(
                "Saved claims:",
                len(saved_claims),
            )


            # ------------------------------------------
            # Correctness evaluation only
            # ------------------------------------------

            evaluation = (
                evaluator.evaluate(
                    case=case,
                    claims=saved_claims,
                )
            )


            # ------------------------------------------
            # Replace ONLY correctness fields
            # ------------------------------------------

            row[
                "correctness_score"
            ] = (
                evaluation.correctness_score
            )

            row[
                "correct_claims"
            ] = (
                evaluation.correct_claims
            )

            row[
                "partially_correct_claims"
            ] = (
                evaluation
                .partially_correct_claims
            )

            row[
                "incorrect_claims"
            ] = (
                evaluation.incorrect_claims
            )

            row[
                "correctness_results"
            ] = (
                build_correctness_results(
                    evaluation
                )
            )


            # ------------------------------------------
            # Persist updated row
            # ------------------------------------------

            output_file.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                )
                +
                "\n"
            )

            output_file.flush()


            processed += 1


            print(
                "Correctness score:",
                evaluation.correctness_score,
            )

            print(
                "Correct:",
                evaluation.correct_claims,
            )

            print(
                "Partial:",
                evaluation.partially_correct_claims,
            )

            print(
                "Incorrect:",
                evaluation.incorrect_claims,
            )


            for claim_result in (
                evaluation.claim_results
            ):

                print(
                    "-",
                    claim_result.verdict.value,
                    "|",
                    claim_result.claim,
                )


    # --------------------------------------------------
    # 6. Final summary
    # --------------------------------------------------

    print()
    print("#" * 70)
    print(
        "CORRECTNESS REJUDGING COMPLETE"
    )
    print("#" * 70)

    print(
        "Processed cases:",
        processed,
    )

    print(
        "Input:",
        INPUT_PATH,
    )

    print(
        "Output:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()