from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    page_content: str
    source: str
    title: str | None = None
    score: float
    metadata: dict = Field(default_factory=dict)
