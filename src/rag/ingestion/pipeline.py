from pathlib import Path

from rag.ingestion.loader import (
    SUPPORTED_EXTENSIONS,
    load_document,
)
from rag.chunking.structure_chunking import MarkdownStructureChunker
from rag.chunking.semantic_chunking import SemanticChunker
from rag.config import settings


DATA_PATH = settings.DATA_PATH

def build_chunks_for_file(file_path: str | Path,
                          semantic_chunker: SemanticChunker | None = None):
    
    path = Path(file_path)

    documents = load_document(path)

    markdown_chunker = MarkdownStructureChunker(
        max_chunk_chars=2000,
        overlap=200,
    )

    if semantic_chunker is None:
        semantic_chunker = SemanticChunker(
            similarity_threshold=0.55,
            max_chunk_chars=2000,
            min_chunk_chars=300,
        )

    all_chunks = []

    for document in documents:

        if document.file_type == "md":
            
            chunks = markdown_chunker.chunk(document)
        else:
            
            chunks = semantic_chunker.chunk(document)

        all_chunks.extend(chunks)

    return all_chunks

def build_chunks(semantic_chunker: SemanticChunker | None = None):

    markdown_chunker = MarkdownStructureChunker(
        max_chunk_chars=2000,
        overlap=200,
    )

    if semantic_chunker is None:
        semantic_chunker = SemanticChunker(
            similarity_threshold=0.55,
            max_chunk_chars=2000,
            min_chunk_chars=300,
        )

    all_chunks = []

    for file_path in DATA_PATH.iterdir():

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        documents = load_document(file_path)

        for document in documents:

            if document.file_type == "md":
                chunks = markdown_chunker.chunk(document)
            else:
                chunks = semantic_chunker.chunk(document)

            all_chunks.extend(chunks)

    return all_chunks

