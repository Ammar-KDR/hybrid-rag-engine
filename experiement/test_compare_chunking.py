# experiment/compare_chunking.py

from rag.ingestion.loader import load_document
from rag.chunking.fixed_size_chunking import FixedChunker
from rag.chunking.structure_chunking import MarkdownStructureChunker
from rag.chunking.semantic_chunking import SemanticChunker


DOCUMENT_PATH = "data/raw/sample_runbook.md"


def print_chunking_results(
    strategy_name: str,
    chunks,
    original_length: int,
):
    print("\n")
    print("=" * 100)
    print(strategy_name.upper())
    print("=" * 100)

    print(f"Number of chunks: {len(chunks)}")
    print(f"Original document characters: {original_length}")

    total_chunk_chars = sum(len(chunk.text) for chunk in chunks)

    print(f"Total characters across chunks: {total_chunk_chars}")
    print(
        f"Extra/duplicated characters: "
        f"{total_chunk_chars - original_length}"
    )

    print("=" * 100)

    for chunk in chunks:
        print()
        print("-" * 100)
        print(f"CHUNK {chunk.chunk_index}")
        print("-" * 100)

        print(f"Length: {len(chunk.text)}")
        print(f"Strategy: {chunk.chunking_strategy}")
        print(f"Source: {chunk.source}")
        print(f"File type: {chunk.file_type}")
        print(f"Metadata: {chunk.metadata}")

        print("\nTEXT:")
        print(chunk.text)

        print()


def main():
    # ---------------------------------------------------------
    # 1. Load the SAME document for all three strategies
    # ---------------------------------------------------------

    documents = load_document(DOCUMENT_PATH)

    if not documents:
        raise RuntimeError("The loader returned no documents.")

    document = documents[0]

    print("=" * 100)
    print("CHUNKING STRATEGY COMPARISON")
    print("=" * 100)

    print(f"Document: {document.source}")
    print(f"File type: {document.file_type}")
    print(f"Original length: {len(document.text)} characters")

    # ---------------------------------------------------------
    # 2. Create the three chunkers
    # ---------------------------------------------------------

    fixed_chunker = FixedChunker(
        chunk_size=500,
        overlap=75,
    )

    structure_chunker = MarkdownStructureChunker(
        max_chunk_chars=500,
        overlap=75,
    )

    semantic_chunker = SemanticChunker(
        similarity_threshold=0.55,
        max_chunk_chars=4000,
    )

    # ---------------------------------------------------------
    # 3. Chunk the same Document
    # ---------------------------------------------------------

    fixed_chunks = fixed_chunker.chunk(document)

    structure_chunks = structure_chunker.chunk(document)

    semantic_chunks = semantic_chunker.chunk(document)

    # ---------------------------------------------------------
    # 4. Print detailed output
    # ---------------------------------------------------------

    print_chunking_results(
        strategy_name="Fixed",
        chunks=fixed_chunks,
        original_length=len(document.text),
    )

    print_chunking_results(
        strategy_name="Structure-Aware Markdown",
        chunks=structure_chunks,
        original_length=len(document.text),
    )

    print_chunking_results(
        strategy_name="Semantic",
        chunks=semantic_chunks,
        original_length=len(document.text),
    )

    # ---------------------------------------------------------
    # 5. Final compact comparison
    # ---------------------------------------------------------

    print("\n")
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    print(f"{'Strategy':<30} {'Chunks':<10} {'Total chars':<15}")
    print("-" * 60)

    print(
        f"{'Fixed':<30} "
        f"{len(fixed_chunks):<10} "
        f"{sum(len(c.text) for c in fixed_chunks):<15}"
    )

    print(
        f"{'Structure-aware':<30} "
        f"{len(structure_chunks):<10} "
        f"{sum(len(c.text) for c in structure_chunks):<15}"
    )

    print(
        f"{'Semantic':<30} "
        f"{len(semantic_chunks):<10} "
        f"{sum(len(c.text) for c in semantic_chunks):<15}"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()