from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DeltaTrend = Literal["improved", "declined", "unchanged", "unavailable"]
GoalChangeStatus = Literal["new", "removed", "modified", "unchanged"]


class MetricDelta(BaseModel):
    """Deterministic difference for one financial metric between two sessions."""

    model_config = ConfigDict(extra="forbid")

    metric_name: str
    metric_key: str
    baseline_value: Decimal | None = None
    current_value: Decimal | None = None
    delta_value: Decimal | None = None
    percentage_change: Decimal | None = None
    trend: DeltaTrend


class RiskShift(BaseModel):
    """Comparison of risk tolerance and score between two sessions."""

    model_config = ConfigDict(extra="forbid")

    baseline_category: str | None = None
    current_category: str | None = None
    baseline_score: int | None = None
    current_score: int | None = None
    score_delta: int | None = None
    category_changed: bool = False


class GoalProgressDelta(BaseModel):
    """Comparison of goal status and shortfall progression."""

    model_config = ConfigDict(extra="forbid")

    goal_id: int
    title: str
    status: GoalChangeStatus
    baseline_target_amount: Decimal | None = None
    current_target_amount: Decimal | None = None
    baseline_shortfall: Decimal | None = None
    current_shortfall: Decimal | None = None
    shortfall_delta: Decimal | None = None


class AnalysisDiffRequest(BaseModel):
    """Request payload to compare two historical analysis snapshots."""

    model_config = ConfigDict(extra="ignore")

    baseline_analysis_id: int = Field(gt=0, description="Earlier analysis session ID")
    current_analysis_id: int = Field(default=0, description="Later analysis session ID")
    comparison_analysis_id: int | None = Field(default=None, description="Alias for current analysis session ID")

    @model_validator(mode="before")
    @classmethod
    def resolve_current_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("current_analysis_id") and data.get("comparison_analysis_id"):
                data["current_analysis_id"] = data["comparison_analysis_id"]
        return data

    @model_validator(mode="after")
    def validate_ids(self) -> "AnalysisDiffRequest":
        if not self.current_analysis_id and self.comparison_analysis_id:
            self.current_analysis_id = self.comparison_analysis_id
        if not self.current_analysis_id or self.current_analysis_id <= 0:
            raise ValueError("Either current_analysis_id or comparison_analysis_id must be provided and greater than 0.")
        return self


class AnalysisDiffExplanation(BaseModel):
    """AI-generated narrative explaining financial trajectory and obsolete recommendations."""

    model_config = ConfigDict(extra="ignore")

    summary_narrative: str = Field(min_length=10, max_length=1500)
    key_improvements: list[str] = Field(min_length=1, max_length=10)
    key_concerns: list[str] = Field(default_factory=list, max_length=10)
    stale_recommendations: list[str] = Field(
        min_length=1,
        max_length=10,
        description="Previous recommendations that are no longer relevant or need revision.",
    )
    updated_strategic_focus: list[str] = Field(min_length=1, max_length=10)
    areas_of_concern: list[str] = Field(default_factory=list, description="Alias for key_concerns")
    obsolete_advice: list[str] = Field(default_factory=list, description="Alias for stale_recommendations")

    @model_validator(mode="after")
    def populate_narrative_aliases(self) -> "AnalysisDiffExplanation":
        if not self.areas_of_concern and self.key_concerns:
            self.areas_of_concern = list(self.key_concerns)
        if not self.obsolete_advice and self.stale_recommendations:
            self.obsolete_advice = list(self.stale_recommendations)
        return self


class AnalysisDiffResponse(BaseModel):
    """Complete financial progress comparison response."""

    model_config = ConfigDict(extra="ignore")

    baseline_analysis_id: int
    current_analysis_id: int
    baseline_id: int | None = None
    current_id: int | None = None
    baseline_created_at: datetime
    current_created_at: datetime
    elapsed_days: int
    metric_deltas: list[MetricDelta]
    risk_shift: RiskShift
    goal_deltas: list[GoalProgressDelta]
    ai_explanation: AnalysisDiffExplanation
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def populate_id_aliases(self) -> "AnalysisDiffResponse":
        if self.baseline_id is None:
            self.baseline_id = self.baseline_analysis_id
        if self.current_id is None:
            self.current_id = self.current_analysis_id
        return self

