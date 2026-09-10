from pathlib import Path
from statistics import mean, median

from rag.ingestion.loader import load_document
from rag.chunking.semantic_chunking import SemanticChunker


DATA_PATH = Path("data/raw")


def build_semantic_chunks():

    chunker = SemanticChunker(
        similarity_threshold=0.55,
        max_chunk_chars=2000,
        min_chunk_chars=300
    )

    all_chunks = []

    for file_path in DATA_PATH.glob("*.md"):

        documents = load_document(
            str(file_path)
        )

        for document in documents:

            chunks = chunker.chunk(
                document
            )

            all_chunks.extend(
                chunks
            )

    return all_chunks


def analyze_chunks(
    chunks,
):

    if not chunks:

        print("No chunks generated.")
        return


    sizes = [
        len(chunk.text)
        for chunk in chunks
    ]


    paragraph_counts = [
        (
            chunk.metadata[
                "end_paragraph"
            ]
            -
            chunk.metadata[
                "start_paragraph"
            ]
            +
            1
        )
        for chunk in chunks
    ]


    print("=" * 60)
    print("SEMANTIC CHUNKING V1 — CORPUS STATISTICS")
    print("=" * 60)

    print(
        "Total semantic chunks:",
        len(chunks),
    )

    print(
        "Average chars:",
        round(
            mean(sizes),
            2,
        ),
    )

    print(
        "Median chars:",
        median(sizes),
    )

    print(
        "Min chars:",
        min(sizes),
    )

    print(
        "Max chars:",
        max(sizes),
    )

    print()

    print(
        "Average paragraphs/chunk:",
        round(
            mean(paragraph_counts),
            2,
        ),
    )

    print(
        "Median paragraphs/chunk:",
        median(
            paragraph_counts
        ),
    )


    singleton_chunks = sum(
        1
        for count in paragraph_counts
        if count == 1
    )


    print(
        "Single-paragraph chunks:",
        singleton_chunks,
    )

    print(
        "Singleton ratio:",
        round(
            singleton_chunks
            /
            len(chunks),
            3,
        ),
    )


    # --------------------------------------------------
    # Markdown heading diagnostic
    # --------------------------------------------------

    heading_only_chunks = [
        chunk
        for chunk in chunks
        if (
            chunk.text.strip().startswith("#")
            and
            "\n"
            not in chunk.text.strip()
        )
    ]


    print()

    print(
        "Heading-only chunks:",
        len(
            heading_only_chunks
        ),
    )


    if heading_only_chunks:

        print()
        print(
            "Examples of heading-only chunks:"
        )

        for chunk in (
            heading_only_chunks[:10]
        ):

            print(
                repr(
                    chunk.text
                )
            )


    # --------------------------------------------------
    # Very small chunk diagnostic
    # --------------------------------------------------

    tiny_chunks = [
        chunk
        for chunk in chunks
        if len(
            chunk.text.strip()
        ) < 100
    ]


    print()

    print(
        "Chunks under 100 chars:",
        len(tiny_chunks),
    )

    print(
        "Tiny-chunk ratio:",
        round(
            len(tiny_chunks)
            /
            len(chunks),
            3,
        ),
    )


    if tiny_chunks:

        print()
        print(
            "Examples of tiny chunks:"
        )

        for chunk in (
            tiny_chunks[:10]
        ):

            print(
                repr(
                    chunk.text
                )
            )


def main():

    chunks = (
        build_semantic_chunks()
    )

    analyze_chunks(
        chunks
    )


if __name__ == "__main__":

    main()