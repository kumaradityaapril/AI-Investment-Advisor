from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    model_config = ConfigDict(extra="ignore")

    question: str = Field(default="", min_length=0, max_length=1000, description="Financial research query")
    query: str | None = Field(default=None, description="Alias for question")
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum tool execution rounds before forcing synthesis",
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_question(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("question") and data.get("query"):
                data["question"] = data["query"]
        return data

    @model_validator(mode="after")
    def validate_question_present(self) -> "ResearchRequest":
        if not self.question and self.query:
            self.question = self.query
        s = self.question.strip()
        if len(s) < 3:
            raise ValueError("Research question must be at least 3 characters long.")
        self.question = s
        return self


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

    model_config = ConfigDict(extra="ignore")

    research_question: str = ""
    summary: str = Field(min_length=10, max_length=3500)
    key_findings: list[str] = Field(min_length=1, max_length=10)
    supporting_evidence: list[EvidenceItem] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list, max_length=10)
    risks_and_limitations: list[str] = Field(default_factory=list, max_length=10)
    researched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Frontend compatibility aliases
    query: str | None = None
    executive_summary: str | None = None
    synthesis: str | None = None
    risk_factors: list[str] | None = None
    regulatory_disclaimer: str | None = None

    @model_validator(mode="after")
    def populate_report_aliases(self) -> "ResearchReport":
        if not self.sources and self.supporting_evidence:
            self.sources = [
                f"{e.source_title} ({e.reference_id})"
                for e in self.supporting_evidence[:10]
            ]
        if not self.query:
            self.query = self.research_question
        if not self.executive_summary:
            self.executive_summary = self.summary
        if not self.synthesis:
            self.synthesis = self.summary
        if not self.risk_factors:
            self.risk_factors = list(self.risks_and_limitations)
        if not self.regulatory_disclaimer:
            self.regulatory_disclaimer = (
                "This research report is compiled autonomously using validated financial citations "
                "and calculations for educational purposes only. It does not constitute certified investment advice."
            )
        return self
