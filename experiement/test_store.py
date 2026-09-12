from rag.ingestion.chunk_store import ChunkStore
from rag.ingestion.model import Chunk


def make_chunk(
    text: str = "hello world",
    index: int = 0,
) -> Chunk:
    return Chunk(
        text=text,
        source="test.md",
        file_type=".md",
        chunk_index=index,
        chunking_strategy="structure",
        metadata={"section": "Test"},
    )


def test_missing_store_returns_empty_list(tmp_path):
    store = ChunkStore(tmp_path / "chunks.jsonl")

    assert store.load_all() == []


def test_replace_all_round_trip(tmp_path):
    store = ChunkStore(tmp_path / "chunks.jsonl")

    chunks = [
        make_chunk("first chunk", 0),
        make_chunk("second chunk", 1),
    ]

    store.replace_all(chunks)

    loaded = store.load_all()

    assert len(loaded) == 2

    assert loaded[0].chunk_id == chunks[0].chunk_id
    assert loaded[0].text == chunks[0].text
    assert loaded[0].metadata == chunks[0].metadata

    assert loaded[1].chunk_id == chunks[1].chunk_id


def test_add_many_preserves_existing_chunks(tmp_path):
    store = ChunkStore(tmp_path / "chunks.jsonl")

    first = make_chunk("first", 0)
    second = make_chunk("second", 1)

    store.add_many([first])
    store.add_many([second])

    loaded = store.load_all()

    assert {chunk.chunk_id for chunk in loaded} == {
        first.chunk_id,
        second.chunk_id,
    }


def test_add_many_is_idempotent(tmp_path):
    store = ChunkStore(tmp_path / "chunks.jsonl")

    chunk = make_chunk()

    store.add_many([chunk])
    store.add_many([chunk])

    loaded = store.load_all()

    assert len(loaded) == 1
    assert loaded[0].chunk_id == chunk.chunk_id