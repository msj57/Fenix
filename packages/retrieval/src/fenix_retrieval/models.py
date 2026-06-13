from pydantic import BaseModel, ConfigDict


class ChunkResult(BaseModel):
    """Chunk recuperado, con los metadatos necesarios para citarlo."""

    model_config = ConfigDict(frozen=True)

    chunk_id: int
    document_id: int
    source_path: str
    title: str
    doc_type: str
    lang: str
    heading_path: str
    content: str
    score: float
