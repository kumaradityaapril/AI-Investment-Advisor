from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


DocumentStatus = Literal["uploaded", "processing", "processed", "failed"]
DocumentIndexingStatus = Literal["pending", "indexing", "indexed", "failed"]


class DocumentResponse(BaseModel):
    """Metadata returned for an uploaded financial document."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str = Field(min_length=1, max_length=255)
    filename: str | None = None
    content_type: str
    file_size_bytes: int = Field(gt=0)
    status: DocumentStatus
    indexing_status: DocumentIndexingStatus = "pending"
    uploaded_at: datetime | None = None
    indexed_at: datetime | None = None
    chunk_count: int = 0
    created_at: datetime

    @model_validator(mode="after")
    def populate_frontend_fields(self) -> "DocumentResponse":
        if not self.filename:
            self.filename = self.original_filename
        if not self.uploaded_at:
            self.uploaded_at = self.created_at
        return self


class DocumentTextResponse(BaseModel):
    """Response containing extracted PDF text."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    status: DocumentStatus
    extracted_text: str = Field(min_length=1)
    created_at: datetime


class DocumentIndexResponse(BaseModel):
    """Response returned after document indexing."""

    id: int
    indexing_status: DocumentIndexingStatus
    indexed_at: datetime | None
    chunk_count: int = Field(ge=0)
