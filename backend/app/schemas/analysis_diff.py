from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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

    model_config = ConfigDict(extra="forbid")

    baseline_analysis_id: int = Field(gt=0, description="Earlier analysis session ID")
    current_analysis_id: int = Field(gt=0, description="Later analysis session ID")


class AnalysisDiffExplanation(BaseModel):
    """AI-generated narrative explaining financial trajectory and obsolete recommendations."""

    model_config = ConfigDict(extra="forbid")

    summary_narrative: str = Field(min_length=10, max_length=1500)
    key_improvements: list[str] = Field(min_length=1, max_length=10)
    key_concerns: list[str] = Field(default_factory=list, max_length=10)
    stale_recommendations: list[str] = Field(
        min_length=1,
        max_length=10,
        description="Previous recommendations that are no longer relevant or need revision.",
    )
    updated_strategic_focus: list[str] = Field(min_length=1, max_length=10)


class AnalysisDiffResponse(BaseModel):
    """Complete financial progress comparison response."""

    model_config = ConfigDict(extra="forbid")

    baseline_analysis_id: int
    current_analysis_id: int
    baseline_created_at: datetime
    current_created_at: datetime
    elapsed_days: int
    metric_deltas: list[MetricDelta]
    risk_shift: RiskShift
    goal_deltas: list[GoalProgressDelta]
    ai_explanation: AnalysisDiffExplanation
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

