from pathlib import Path

from rag.ingestion.loader import (
    SUPPORTED_EXTENSIONS,
    load_document,
)
from rag.chunking.structure_chunking import MarkdownStructureChunker
from rag.chunking.semantic_chunking import SemanticChunker
from rag.chunking.arabic_chunker import ArabicGovernmentChunker
from rag.nlp.arabic import is_arabic_text
from rag.config import settings


DATA_PATH = settings.DATA_PATH

def build_chunks_for_file(file_path: str | Path,
                          semantic_chunker: SemanticChunker | None = None,
                          arabic_chunker: ArabicGovernmentChunker | None = None):
    
    path = Path(file_path)

    documents = load_document(path)

    markdown_chunker = MarkdownStructureChunker(
        max_chunk_chars=2000,
        overlap=200,
    )

    if arabic_chunker is None:
        arabic_chunker = ArabicGovernmentChunker(
            max_chunk_chars=1200,
            overlap=200,
            inject_heading_context=True,
        )

    if semantic_chunker is None:
        semantic_chunker = SemanticChunker(
            similarity_threshold=0.55,
            max_chunk_chars=2000,
            min_chunk_chars=300,
        )

    all_chunks = []

    for document in documents:

        if is_arabic_text(document.text):
            chunks = arabic_chunker.chunk(document)
        elif document.file_type == "md":
            chunks = markdown_chunker.chunk(document)
        else:
            chunks = semantic_chunker.chunk(document)

        all_chunks.extend(chunks)

    return all_chunks

def build_chunks(
    semantic_chunker: SemanticChunker | None = None,
    arabic_chunker: ArabicGovernmentChunker | None = None,
    data_path: Path | None = None,
):

    markdown_chunker = MarkdownStructureChunker(
        max_chunk_chars=2000,
        overlap=200,
    )

    if arabic_chunker is None:
        arabic_chunker = ArabicGovernmentChunker(
            max_chunk_chars=1200,
            overlap=200,
            inject_heading_context=True,
        )

    if semantic_chunker is None:
        semantic_chunker = SemanticChunker(
            similarity_threshold=0.55,
            max_chunk_chars=2000,
            min_chunk_chars=300,
        )

    all_chunks = []
    target_path = Path(data_path) if data_path else DATA_PATH

    for file_path in sorted(target_path.rglob("*")):

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        documents = load_document(file_path)

        for document in documents:

            if is_arabic_text(document.text):
                chunks = arabic_chunker.chunk(document)
            elif document.file_type == "md":
                chunks = markdown_chunker.chunk(document)
            else:
                chunks = semantic_chunker.chunk(document)

            all_chunks.extend(chunks)

    return all_chunks


