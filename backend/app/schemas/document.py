
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DocumentStatus = Literal["uploaded", "processing", "processed", "failed"]


class DocumentResponse(BaseModel):
    """Metadata returned for an uploaded financial document."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str = Field(min_length=1, max_length=255)
    content_type: str
    file_size_bytes: int = Field(gt=0)
    status: DocumentStatus
    created_at: datetime
