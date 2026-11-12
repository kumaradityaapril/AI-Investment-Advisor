from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalysisHistorySummary(BaseModel):
    """Brief summary of a previous advisor analysis session for listing."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    question: str
    advisor_model: str
    overall_assessment: str
    recommendations_count: int
    created_at: datetime


class AnalysisHistoryDetail(BaseModel):
    """Full snapshot of a previous advisor analysis session."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    question: str
    advisor_model: str
    financial_context_snapshot: dict[str, Any]
    advisor_response_snapshot: dict[str, Any]
    evidence_references: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime


class AnalysisHistoryListResponse(BaseModel):
    """Paginated list of saved advisor analysis sessions."""

    model_config = ConfigDict(from_attributes=True)

    items: list[AnalysisHistorySummary]
    total: int
    skip: int
    limit: int

