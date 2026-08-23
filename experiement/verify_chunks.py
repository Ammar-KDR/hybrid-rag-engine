import json
from pathlib import Path


CHUNKS_FILE = Path("data/evaluation/chunks.json")
DATASET_FILE = Path("data/evaluation/retrieval_dataset.json")


def load_json(path: Path):
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def validate_dataset():

    chunks = load_json(CHUNKS_FILE)
    dataset = load_json(DATASET_FILE)

    available_chunk_ids = {
        chunk["chunk_id"]
        for chunk in chunks
    }

    missing_ids = []

    total_expected = 0

    for item in dataset:

        for chunk_id in item["expected_chunk_ids"]:

            total_expected += 1

            if chunk_id not in available_chunk_ids:
                missing_ids.append(
                    {
                        "question_id": item["id"],
                        "question": item["question"],
                        "missing_chunk_id": chunk_id,
                    }
                )

    print("=" * 60)

    print(
        f"Total evaluation questions: {len(dataset)}"
    )

    print(
        f"Total expected chunk references: {total_expected}"
    )

    print(
        f"Available chunks: {len(available_chunk_ids)}"
    )

    print("=" * 60)


    if missing_ids:

        print(
            "Missing chunk IDs found:"
        )

        for item in missing_ids:

            print("-" * 60)

            print(
                f"Question ID: {item['question_id']}"
            )

            print(
                f"Question: {item['question']}"
            )

            print(
                f"Missing ID: {item['missing_chunk_id']}"
            )

        print()

        print(
            f"FAILED: {len(missing_ids)} invalid references"
        )

    else:

        print(
            "SUCCESS: All expected chunk IDs exist."
        )


if __name__ == "__main__":
    validate_dataset()