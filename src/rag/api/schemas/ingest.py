from pydantic import BaseModel


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    ingested_at: str
    chunking_strategy: str
    duplicate: bool