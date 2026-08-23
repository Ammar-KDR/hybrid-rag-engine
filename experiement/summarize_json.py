import json


INPUT_FILE = "data/evaluation/chunks.json"


def summarize():

    with open(
        INPUT_FILE,
        encoding="utf-8"
    ) as f:
        chunks = json.load(f)

    for i, chunk in enumerate(chunks):

        print("=" * 60)

        print(f"Index: {i}")

        print(
            f"Chunk ID: {chunk['chunk_id']}"
        )

        print(
            f"Source: {chunk['source']}"
        )

        print(
            f"Heading: {chunk.get('heading')}"
        )


if __name__ == "__main__":
    summarize()