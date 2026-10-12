#!/usr/bin/env python3
"""Migrate Canonical Metadata

Enriches data/indexes/chunks.jsonl and Qdrant payloads with:
- document_id (from registry)
- filename (clean display name)
- file_type
- chunk_index
"""

import json
import sys
import uuid
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rag.config import settings
from qdrant_client import QdrantClient


def migrate():
    reg_path = settings.REGISTRY_PATH
    chunk_path = settings.CHUNK_STORE_PATH
    qdrant_path = settings.QDRANT_LOCAL_PATH

    print(f"Loading registry from {reg_path}...")
    with reg_path.open("r", encoding="utf-8") as f:
        reg_data = json.load(f)

    reg_map = {doc["filename"]: doc["document_id"] for doc in reg_data.get("documents", [])}
    print(f"Found {len(reg_map)} documents in registry.")

    # 1. Update chunks.jsonl
    print(f"Enriching chunks in {chunk_path}...")
    updated_chunks = []
    with chunk_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            chunk = json.loads(line)
            source_filename = Path(chunk["source"]).name
            doc_id = reg_map.get(source_filename)
            if doc_id:
                chunk["metadata"]["document_id"] = doc_id
                chunk["metadata"]["filename"] = source_filename
                chunk["metadata"]["file_type"] = chunk["file_type"]
                chunk["metadata"]["chunk_index"] = chunk["chunk_index"]
            updated_chunks.append(chunk)

    temp_path = chunk_path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        for chunk in updated_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    temp_path.replace(chunk_path)
    print(f"Successfully updated {len(updated_chunks)} chunks in {chunk_path}.")

    # 2. Update Qdrant vector store
    print(f"Connecting to Qdrant at {qdrant_path}...")
    client = QdrantClient(path=str(qdrant_path))
    collection = settings.QDRANT_COLLECTION

    count = 0
    for chunk in updated_chunks:
        chunk_id = chunk["chunk_id"]
        source_filename = Path(chunk["source"]).name
        doc_id = reg_map.get(source_filename)
        if not doc_id:
            continue

        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
        client.set_payload(
            collection_name=collection,
            payload={
                "document_id": doc_id,
                "filename": source_filename,
                "file_type": chunk["file_type"],
                "chunk_index": chunk["chunk_index"],
            },
            points=[point_id],
        )
        count += 1

    print(f"Successfully updated {count} points in Qdrant collection '{collection}'.")
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
