from rag.ingestion.model import Document
from rag.chunking.structure_chunking import MarkdownStructureChunker
doc = Document(
    text="""# Kubernetes

Short intro.

## Pods

ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ

### HI TESTING THIS
  rashahsh 
""",
    source="test.md",
    file_type="md",
)

chunker = MarkdownStructureChunker(
    max_chunk_chars=30,
    overlap=5,
)

chunks = chunker.chunk(doc)

for chunk in chunks:
    print("INDEX:", chunk.chunk_index)
    print("TEXT:", repr(chunk.text))
    print("METADATA:", chunk.metadata)
    print()