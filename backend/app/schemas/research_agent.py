from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

EvidenceSourceType = Literal[
    "financial_document",
    "financial_calculation",
    "financial_information",
]


class EvidenceItem(BaseModel):
    """Piece of verified evidence gathered by a research tool."""

    source_type: EvidenceSourceType
    source_title: str = Field(description="Name or title of the source")
    reference_id: str | None = Field(
        default=None,
        description="Chunk ID, document ID, calculation identifier, or rule reference",
    )
    content_snippet: str = Field(description="Key excerpt, calculation result, or factual finding")
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional relevance or retrieval score",
    )


class ResearchRequest(BaseModel):
    """User request to initiate an autonomous research workflow."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=1000, description="Financial research query")
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum tool execution rounds before forcing synthesis",
    )


class ToolSelectionDecision(BaseModel):
    """Structured decision by agent planner choosing next tool or concluding research."""

    action: Literal["use_tool", "finish_research"]
    tool_name: Literal[
        "search_financial_documents",
        "calculate_financial_metrics",
        "search_financial_information",
    ] | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = Field(min_length=5, max_length=500)


class EvidenceEvaluationResult(BaseModel):
    """Structured evaluation of evidence sufficiency."""

    is_sufficient: bool
    reasoning: str = Field(min_length=5, max_length=500)
    missing_information: str | None = None


class ResearchReport(BaseModel):
    """Final grounded research synthesis backed by collected evidence."""

    research_question: str
    summary: str = Field(min_length=10, max_length=2000)
    key_findings: list[str] = Field(min_length=1, max_length=10)
    supporting_evidence: list[EvidenceItem] = Field(default_factory=list)
    sources: list[str] = Field(min_length=1, max_length=10)
    risks_and_limitations: list[str] = Field(default_factory=list, max_length=10)
    researched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
