import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

CHUNKS_PATH = Path(
    "data/evaluation/chunks2.json"
)

DATASET_PATH = Path(
    "data/evaluation/hybrid_retrieval_dataset.json"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path: Path):

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# EXTRACT CHUNK IDS
# ============================================================

def extract_available_chunk_ids(chunks_data):

    """
    Supports common structures such as:

    [
        {
            "chunk_id": "...",
            "text": "...",
            ...
        }
    ]

    or:

    {
        "chunks": [
            {
                "chunk_id": "...",
                ...
            }
        ]
    }
    """

    if isinstance(chunks_data, dict):

        if "chunks" in chunks_data:
            chunks = chunks_data["chunks"]
        else:
            raise ValueError(
                "Could not find 'chunks' key "
                "inside chunks JSON."
            )

    elif isinstance(chunks_data, list):

        chunks = chunks_data

    else:
        raise ValueError(
            "Unexpected chunks JSON structure."
        )

    chunk_ids = set()

    missing_chunk_id_field = []

    for index, chunk in enumerate(chunks):

        chunk_id = chunk.get("chunk_id")

        if not chunk_id:
            missing_chunk_id_field.append(index)
            continue

        chunk_ids.add(chunk_id)

    if missing_chunk_id_field:
        print(
            "\nWARNING:"
            f" {len(missing_chunk_id_field)} chunks "
            "do not contain a chunk_id."
        )

        print(
            "Indexes:",
            missing_chunk_id_field,
        )

    return chunk_ids


# ============================================================
# EXTRACT EVALUATION CASES
# ============================================================

def extract_evaluation_cases(dataset_data):

    """
    Supports either:

    [
        {
            "question": "...",
            "expected_chunk_ids": [...]
        }
    ]

    or:

    {
        "questions": [...]
    }

    or:

    {
        "cases": [...]
    }
    """

    if isinstance(dataset_data, list):
        return dataset_data

    if isinstance(dataset_data, dict):

        if "questions" in dataset_data:
            return dataset_data["questions"]

        if "cases" in dataset_data:
            return dataset_data["cases"]

        if "dataset" in dataset_data:
            return dataset_data["dataset"]

    raise ValueError(
        "Unexpected evaluation dataset structure."
    )


# ============================================================
# VALIDATE GOLDEN REFERENCES
# ============================================================

def validate_dataset(
    evaluation_cases,
    available_chunk_ids,
):

    valid_cases = []

    partially_valid_cases = []

    invalid_cases = []

    malformed_cases = []

    all_referenced_ids = set()

    for index, case in enumerate(
        evaluation_cases
    ):

        question = case.get("question")

        expected_ids = case.get(
            "expected_chunk_ids"
        )

        # ----------------------------------------------------
        # Basic schema validation
        # ----------------------------------------------------

        if not question:

            malformed_cases.append(
                {
                    "index": index,
                    "reason": "Missing question",
                    "case": case,
                }
            )

            continue

        if not expected_ids:

            malformed_cases.append(
                {
                    "index": index,
                    "question": question,
                    "reason": (
                        "Missing or empty "
                        "expected_chunk_ids"
                    ),
                }
            )

            continue

        if not isinstance(
            expected_ids,
            list,
        ):

            malformed_cases.append(
                {
                    "index": index,
                    "question": question,
                    "reason": (
                        "expected_chunk_ids "
                        "must be a list"
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Check IDs
        # ----------------------------------------------------

        expected_set = set(
            expected_ids
        )

        all_referenced_ids.update(
            expected_set
        )

        existing_ids = (
            expected_set
            & available_chunk_ids
        )

        missing_ids = (
            expected_set
            - available_chunk_ids
        )

        # ----------------------------------------------------
        # Fully valid
        # ----------------------------------------------------

        if (
            existing_ids
            and not missing_ids
        ):

            valid_cases.append(
                {
                    "question": question,
                    "expected_ids": expected_set,
                }
            )

        # ----------------------------------------------------
        # Partially valid
        #
        # At least one golden ID exists,
        # but another one is stale/missing.
        # ----------------------------------------------------

        elif existing_ids and missing_ids:

            partially_valid_cases.append(
                {
                    "question": question,
                    "existing_ids": existing_ids,
                    "missing_ids": missing_ids,
                }
            )

        # ----------------------------------------------------
        # Fully invalid
        #
        # None of the golden evidence exists
        # in the current corpus.
        # ----------------------------------------------------

        else:

            invalid_cases.append(
                {
                    "question": question,
                    "missing_ids": missing_ids,
                }
            )

    return {
        "valid": valid_cases,
        "partial": partially_valid_cases,
        "invalid": invalid_cases,
        "malformed": malformed_cases,
        "referenced_ids": all_referenced_ids,
    }


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    results,
    available_chunk_ids,
    total_cases,
):

    valid = results["valid"]
    partial = results["partial"]
    invalid = results["invalid"]
    malformed = results["malformed"]

    print("\n")
    print("=" * 80)
    print("EVALUATION DATASET INTEGRITY CHECK")
    print("=" * 80)

    print(
        f"Corpus chunk IDs: "
        f"{len(available_chunk_ids)}"
    )

    print(
        f"Evaluation cases: "
        f"{total_cases}"
    )

    print(
        f"Fully valid cases: "
        f"{len(valid)}"
    )

    print(
        f"Partially valid cases: "
        f"{len(partial)}"
    )

    print(
        f"Invalid cases: "
        f"{len(invalid)}"
    )

    print(
        f"Malformed cases: "
        f"{len(malformed)}"
    )

    # --------------------------------------------------------
    # Partially valid
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("PARTIALLY VALID CASES")
    print("=" * 80)

    if not partial:
        print("None")

    else:

        for item in partial:

            print(
                f"\nQuestion: "
                f"{item['question']}"
            )

            print("Existing IDs:")

            for chunk_id in item[
                "existing_ids"
            ]:
                print(
                    f"  ✓ {chunk_id}"
                )

            print("Missing IDs:")

            for chunk_id in item[
                "missing_ids"
            ]:
                print(
                    f"  ✗ {chunk_id}"
                )

    # --------------------------------------------------------
    # Fully invalid
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print(
        "INVALID CASES — "
        "NO GOLDEN EVIDENCE EXISTS"
    )
    print("=" * 80)

    if not invalid:
        print("None")

    else:

        for item in invalid:

            print(
                f"\nQuestion: "
                f"{item['question']}"
            )

            print(
                "Missing expected chunk IDs:"
            )

            for chunk_id in item[
                "missing_ids"
            ]:

                print(
                    f"  ✗ {chunk_id}"
                )

    # --------------------------------------------------------
    # Malformed
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("MALFORMED CASES")
    print("=" * 80)

    if not malformed:
        print("None")

    else:

        for item in malformed:

            print(
                f"\nIndex: "
                f"{item['index']}"
            )

            print(
                f"Reason: "
                f"{item['reason']}"
            )

            if "question" in item:

                print(
                    f"Question: "
                    f"{item['question']}"
                )


# ============================================================
# MAIN
# ============================================================

def main():

    chunks_data = load_json(
        CHUNKS_PATH
    )

    dataset_data = load_json(
        DATASET_PATH
    )

    available_chunk_ids = (
        extract_available_chunk_ids(
            chunks_data
        )
    )

    evaluation_cases = (
        extract_evaluation_cases(
            dataset_data
        )
    )

    results = validate_dataset(
        evaluation_cases,
        available_chunk_ids,
    )

    print_report(
        results=results,
        available_chunk_ids=available_chunk_ids,
        total_cases=len(
            evaluation_cases
        ),
    )

    # --------------------------------------------------------
    # Final validation result
    # --------------------------------------------------------

    invalid_count = (
        len(results["partial"])
        + len(results["invalid"])
        + len(results["malformed"])
    )

    print("\n")
    print("=" * 80)

    if invalid_count == 0:

        print(
            "PASS: Evaluation dataset is valid "
            "against the current corpus."
        )

        print("=" * 80)

        return

    print(
        "FAIL: Evaluation dataset contains "
        f"{invalid_count} problematic case(s)."
    )

    print(
        "\nDo NOT trust retrieval metrics "
        "until these cases are fixed."
    )

    print("=" * 80)

    raise SystemExit(1)


if __name__ == "__main__":
    main()