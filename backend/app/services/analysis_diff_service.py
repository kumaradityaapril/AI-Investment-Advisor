from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis_history import AnalysisHistory
from app.schemas.analysis_diff import (
    AnalysisDiffExplanation,
    AnalysisDiffRequest,
    AnalysisDiffResponse,
    GoalProgressDelta,
    MetricDelta,
    RiskShift,
)
from app.services.advisor_output_validation_service import (
    UNSAFE_FINANCIAL_PATTERNS,
    _is_negated,
)
from app.services.analysis_history_service import get_user_analysis_by_id

logger = logging.getLogger(__name__)


class AnalysisDiffError(Exception):
    """Raised when analysis diff generation fails."""


def _get_gemini_client() -> genai.Client:
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={
            "api_version": "v1beta",
            "timeout": 30000,
        },
    )


def _to_decimal(val: Any) -> Decimal | None:
    if val is None:
        return None
    try:
        dec = Decimal(str(val))
        return dec if dec.is_finite() else None
    except Exception:
        return None


def calculate_metric_deltas(
    baseline_ctx: dict[str, Any],
    current_ctx: dict[str, Any],
) -> list[MetricDelta]:
    """Calculate deterministic differences for primary financial metrics."""

    b_metrics = baseline_ctx.get("metrics") or {}
    c_metrics = current_ctx.get("metrics") or {}
    b_profile = baseline_ctx.get("profile") or {}
    c_profile = current_ctx.get("profile") or {}

    metric_specs = [
        ("Monthly Income", "monthly_income", b_profile.get("monthly_income"), c_profile.get("monthly_income"), False),
        ("Monthly Expenses", "monthly_expenses", b_profile.get("monthly_expenses"), c_profile.get("monthly_expenses"), True),
        ("Monthly Surplus", "monthly_surplus", b_metrics.get("monthly_surplus"), c_metrics.get("monthly_surplus"), False),
        ("Savings Rate", "savings_rate_percent", b_metrics.get("savings_rate_percent"), c_metrics.get("savings_rate_percent"), False),
        ("Expense Ratio", "expense_ratio_percent", b_metrics.get("expense_ratio_percent"), c_metrics.get("expense_ratio_percent"), True),
    ]

    deltas: list[MetricDelta] = []
    for name, key, b_raw, c_raw, lower_is_better in metric_specs:
        b_val = _to_decimal(b_raw)
        c_val = _to_decimal(c_raw)

        if b_val is None and c_val is None:
            trend = "unavailable"
            delta = None
            pct_change = None
        elif b_val is None or c_val is None:
            trend = "unavailable"
            delta = None
            pct_change = None
        else:
            delta = c_val - b_val
            pct_change = (
                Decimal(round((delta / abs(b_val)) * Decimal("100"), 2))
                if b_val != Decimal("0")
                else None
            )

            if delta == Decimal("0"):
                trend = "unchanged"
            elif (delta > Decimal("0") and not lower_is_better) or (delta < Decimal("0") and lower_is_better):
                trend = "improved"
            else:
                trend = "declined"

        deltas.append(
            MetricDelta(
                metric_name=name,
                metric_key=key,
                baseline_value=b_val,
                current_value=c_val,
                delta_value=delta,
                percentage_change=pct_change,
                trend=trend,
            )
        )

    return deltas


def calculate_risk_shift(
    baseline_ctx: dict[str, Any],
    current_ctx: dict[str, Any],
) -> RiskShift:
    """Compare investor risk assessments across snapshots."""

    b_risk = baseline_ctx.get("risk_assessment") or {}
    c_risk = current_ctx.get("risk_assessment") or {}

    b_cat = b_risk.get("risk_category")
    c_cat = c_risk.get("risk_category")
    b_score = b_risk.get("risk_score")
    c_score = c_risk.get("risk_score")

    score_delta = None
    if isinstance(b_score, int) and isinstance(c_score, int):
        score_delta = c_score - b_score

    changed = (b_cat != c_cat) or (score_delta is not None and score_delta != 0)

    return RiskShift(
        baseline_category=b_cat,
        current_category=c_cat,
        baseline_score=b_score,
        current_score=c_score,
        score_delta=score_delta,
        category_changed=changed,
    )


def calculate_goal_deltas(
    baseline_ctx: dict[str, Any],
    current_ctx: dict[str, Any],
) -> list[GoalProgressDelta]:
    """Compare goal status and shortfall progression."""

    b_goals = {
        g.get("goal_id"): g
        for g in baseline_ctx.get("goal_analysis", [])
        if g.get("goal_id") is not None
    }
    c_goals = {
        g.get("goal_id"): g
        for g in current_ctx.get("goal_analysis", [])
        if g.get("goal_id") is not None
    }

    all_ids = set(b_goals.keys()) | set(c_goals.keys())
    deltas: list[GoalProgressDelta] = []

    for gid in sorted(all_ids):
        b_item = b_goals.get(gid)
        c_item = c_goals.get(gid)

        if b_item is not None and c_item is None:
            title = b_item.get("goal_title", f"Goal {gid}")
            status = "removed"
            b_target = _to_decimal(b_item.get("target_amount"))
            b_short = _to_decimal(b_item.get("monthly_contribution_shortfall"))
            deltas.append(
                GoalProgressDelta(
                    goal_id=gid,
                    title=title,
                    status=status,
                    baseline_target_amount=b_target,
                    baseline_shortfall=b_short,
                )
            )
        elif c_item is not None and b_item is None:
            title = c_item.get("goal_title", f"Goal {gid}")
            status = "new"
            c_target = _to_decimal(c_item.get("target_amount"))
            c_short = _to_decimal(c_item.get("monthly_contribution_shortfall"))
            deltas.append(
                GoalProgressDelta(
                    goal_id=gid,
                    title=title,
                    status=status,
                    current_target_amount=c_target,
                    current_shortfall=c_short,
                )
            )
        elif b_item is not None and c_item is not None:
            title = c_item.get("goal_title") or b_item.get("goal_title") or f"Goal {gid}"
            b_short = _to_decimal(b_item.get("monthly_contribution_shortfall"))
            c_short = _to_decimal(c_item.get("monthly_contribution_shortfall"))
            short_delta = None
            if b_short is not None and c_short is not None:
                short_delta = c_short - b_short

            status = "modified" if short_delta and short_delta != Decimal("0") else "unchanged"
            deltas.append(
                GoalProgressDelta(
                    goal_id=gid,
                    title=title,
                    status=status,
                    baseline_shortfall=b_short,
                    current_shortfall=c_short,
                    shortfall_delta=short_delta,
                )
            )

    return deltas


def _validate_diff_explanation_safety(explanation: AnalysisDiffExplanation) -> None:
    texts = [
        explanation.summary_narrative,
        *explanation.key_improvements,
        *explanation.key_concerns,
        *explanation.stale_recommendations,
        *explanation.updated_strategic_focus,
    ]
    for text in texts:
        for pattern in UNSAFE_FINANCIAL_PATTERNS:
            for match in pattern.finditer(text):
                if _is_negated(text, match.start()):
                    continue
                raise AnalysisDiffError(
                    "Diff explanation contains disallowed certainty or risk-free language."
                )


def generate_diff_explanation(
    metric_deltas: list[MetricDelta],
    risk_shift: RiskShift,
    goal_deltas: list[GoalProgressDelta],
    baseline_recs: list[dict[str, Any]],
    current_recs: list[dict[str, Any]],
    elapsed_days: int,
    client: genai.Client | None = None,
) -> AnalysisDiffExplanation:
    """Generate structured memory narrative analyzing changes and obsolete advice."""

    if client is None:
        try:
            client = _get_gemini_client()
        except Exception as exc:
            raise AnalysisDiffError(
                f"Failed to initialize Gemini client: {exc}"
            ) from exc

    diff_context = {
        "elapsed_days": elapsed_days,
        "metrics_diff": [m.model_dump(mode="json") for m in metric_deltas],
        "risk_shift": risk_shift.model_dump(mode="json"),
        "goals_diff": [g.model_dump(mode="json") for g in goal_deltas],
        "baseline_previous_recommendations": [
            {"title": r.get("title"), "suggested_action": r.get("suggested_action")}
            for r in baseline_recs
        ],
        "current_recommendations": [
            {"title": r.get("title"), "suggested_action": r.get("suggested_action")}
            for r in current_recs
        ],
    }

    prompt = f"""You are an expert AI Investment Advisor comparing two historical financial snapshots of the same investor.

FINANCIAL CHANGE DATA:
{json.dumps(diff_context, indent=2)}

INSTRUCTIONS:
1. Explain how the investor's financial health, cash flow, and risk posture changed over the elapsed period ({elapsed_days} days).
2. Highlight key improvements (e.g. higher surplus, improved savings rate, narrowed goal shortfall).
3. Identify any concerns (e.g. rising expense ratio, enlarged deficit).
4. CRITICAL: Identify which previous recommendations from the baseline session are now STALE, OBSOLETE, or need adjustment due to the changes in their financial context.
5. Provide updated strategic focus points going forward.
6. Return your analysis matching the AnalysisDiffExplanation schema."""

    try:
        response = client.models.generate_content(
            model=settings.advisor_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=3000,
                response_mime_type="application/json",
                response_schema=AnalysisDiffExplanation,
            ),
        )
    except Exception as exc:
        logger.exception("Failed to generate diff explanation.")
        raise AnalysisDiffError(
            f"Failed to generate diff explanation: {exc}"
        ) from exc

    if response is None:
        raise AnalysisDiffError("Gemini returned an empty response.")

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, AnalysisDiffExplanation):
        explanation = parsed
    else:
        text = getattr(response, "text", None)
        if not text:
            raise AnalysisDiffError("Gemini returned an empty text.")
        try:
            explanation = AnalysisDiffExplanation.model_validate_json(text)
        except ValidationError as exc:
            raise AnalysisDiffError(f"Validation failed on diff explanation: {exc}") from exc

    _validate_diff_explanation_safety(explanation)
    return explanation


def compute_analysis_diff(
    db: Session,
    user_id: int,
    request: AnalysisDiffRequest,
    client: genai.Client | None = None,
) -> AnalysisDiffResponse:
    """
    Compare two historical analysis snapshots, compute deterministic deltas,
    and generate explainable memory narrative.
    """
    baseline = get_user_analysis_by_id(db, user_id=user_id, analysis_id=request.baseline_analysis_id)
    current = get_user_analysis_by_id(db, user_id=user_id, analysis_id=request.current_analysis_id)

    if baseline is None:
        raise ValueError(f"Baseline analysis {request.baseline_analysis_id} not found.")
    if current is None:
        raise ValueError(f"Current analysis {request.current_analysis_id} not found.")

    # Ensure baseline is the chronologically earlier one
    if baseline.created_at > current.created_at:
        baseline, current = current, baseline

    elapsed_days = max(0, (current.created_at.date() - baseline.created_at.date()).days)

    b_ctx = baseline.financial_context_snapshot or {}
    c_ctx = current.financial_context_snapshot or {}
    b_resp = baseline.advisor_response_snapshot or {}
    c_resp = current.advisor_response_snapshot or {}

    metric_deltas = calculate_metric_deltas(b_ctx, c_ctx)
    risk_shift = calculate_risk_shift(b_ctx, c_ctx)
    goal_deltas = calculate_goal_deltas(b_ctx, c_ctx)

    b_recs = b_resp.get("recommendations", [])
    c_recs = c_resp.get("recommendations", [])

    ai_explanation = generate_diff_explanation(
        metric_deltas=metric_deltas,
        risk_shift=risk_shift,
        goal_deltas=goal_deltas,
        baseline_recs=b_recs,
        current_recs=c_recs,
        elapsed_days=elapsed_days,
        client=client,
    )

    return AnalysisDiffResponse(
        baseline_analysis_id=baseline.id,
        current_analysis_id=current.id,
        baseline_created_at=baseline.created_at,
        current_created_at=current.created_at,
        elapsed_days=elapsed_days,
        metric_deltas=metric_deltas,
        risk_shift=risk_shift,
        goal_deltas=goal_deltas,
        ai_explanation=ai_explanation,
    )

