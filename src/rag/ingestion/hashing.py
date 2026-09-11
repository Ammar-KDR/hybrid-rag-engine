import hashlib


def create_chunk_id(
    text: str,
    source: str,
    chunk_index: int,
) -> str:
    content = f"{source}:{chunk_index}:{text}"

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

def create_document_id(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()