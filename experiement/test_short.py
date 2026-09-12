from rag.chunking.semantic_chunking import SemanticChunker
from rag.ingestion.pipeline import build_chunks_for_file


def test_short_meaningful_text_document_produces_chunk(tmp_path):
    file_path = tmp_path / "short.txt"

    file_path.write_text(
        "Project Atlas uses port 8743.",
        encoding="utf-8",
    )

    # A one-paragraph document never needs model.encode(),
    # so an injected dummy object is enough for this test.
    semantic_chunker = SemanticChunker(
        model=object(),
        similarity_threshold=0.55,
        max_chunk_chars=2000,
        min_chunk_chars=300,
    )

    chunks = build_chunks_for_file(
        file_path,
        semantic_chunker=semantic_chunker,
    )

    assert len(chunks) == 1
    assert chunks[0].text == "Project Atlas uses port 8743."