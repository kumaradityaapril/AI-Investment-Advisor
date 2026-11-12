from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Callable
from pydantic import BaseModel, Field

from app.evaluation.dataset import DEFAULT_EVALUATION_DATASET, EvaluationTestCase
from app.evaluation.metrics import (
    MetricResult,
    evaluate_disclaimer_compliance,
    evaluate_financial_accuracy,
    evaluate_groundedness,
    evaluate_required_elements,
    evaluate_safety_compliance,
)

logger = logging.getLogger(__name__)


class CaseEvaluationResult(BaseModel):
    """Detailed evaluation result for one test case."""

    case_id: str
    category: str
    passed: bool
    overall_score: float = Field(ge=0.0, le=1.0)
    metrics: list[MetricResult]
    failure_reasons: list[str] = Field(default_factory=list)


class EvaluationSuiteReport(BaseModel):
    """Comprehensive benchmark evaluation report across all test cases."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_accuracy_rate: float
    category_scores: dict[str, float]
    case_results: list[CaseEvaluationResult]
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        """Render report as a markdown summary table."""
        lines = [
            "# AI Evaluation Benchmark Report",
            f"**Evaluated At:** {self.evaluated_at.isoformat()}",
            f"**Total Cases:** {self.total_cases} | **Passed:** {self.passed_cases} | **Failed:** {self.failed_cases}",
            f"**Overall Accuracy:** {round(self.overall_accuracy_rate * 100, 1)}%\n",
            "## Category Breakdown",
            "| Category | Score |",
            "|---|---|",
        ]
        for cat, score in self.category_scores.items():
            lines.append(f"| {cat} | {round(score * 100, 1)}% |")

        lines.extend([
            "\n## Case Details",
            "| Case ID | Category | Status | Score | Notes |",
            "|---|---|---|---|---|",
        ])
        for c in self.case_results:
            status = "✅ PASS" if c.passed else "❌ FAIL"
            reasons = "; ".join(c.failure_reasons) if c.failure_reasons else "All criteria satisfied"
            lines.append(f"| {c.case_id} | {c.category} | {status} | {round(c.overall_score * 100, 1)}% | {reasons} |")

        return "\n".join(lines)


def evaluate_single_response(
    case: EvaluationTestCase,
    response: dict[str, Any],
) -> CaseEvaluationResult:
    """Evaluate one AI Advisor response against an EvaluationTestCase."""
    metric_results: list[MetricResult] = []
    failure_reasons: list[str] = []

    # 1. Full text assembly
    text_parts = [
        response.get("overall_assessment") or "",
        " ".join(response.get("key_findings") or []),
        " ".join((r.get("explanation", "") for r in response.get("recommendations") or [])),
        " ".join(response.get("risk_considerations") or []),
        " ".join(response.get("limitations") or []),
        response.get("disclaimer") or "",
    ]
    full_text = " ".join(text_parts)

    # 2. Safety compliance
    safety = evaluate_safety_compliance(full_text)
    metric_results.append(safety)
    if not safety.passed:
        failure_reasons.append(safety.details)

    # 3. Disclaimer compliance
    disclaimer = evaluate_disclaimer_compliance(response.get("disclaimer"))
    metric_results.append(disclaimer)
    if not disclaimer.passed:
        failure_reasons.append(disclaimer.details)

    # 4. Financial accuracy
    if case.ground_truth_claims:
        fin_acc = evaluate_financial_accuracy(
            claims=response.get("financial_claims") or [],
            ground_truth=case.ground_truth_claims,
        )
        metric_results.append(fin_acc)
        if not fin_acc.passed:
            failure_reasons.append(fin_acc.details)

    # 5. Groundedness against context
    ctx_metrics = case.financial_context.get("metrics") or {}
    grounded = evaluate_groundedness(
        claims=response.get("financial_claims") or [],
        context_metrics=ctx_metrics,
    )
    metric_results.append(grounded)
    if not grounded.passed:
        failure_reasons.append(grounded.details)

    # 6. Required elements
    if case.required_elements:
        req_el = evaluate_required_elements(full_text, case.required_elements)
        metric_results.append(req_el)
        if not req_el.passed:
            failure_reasons.append(req_el.details)

    # 7. Disallowed terms
    for term in case.disallowed_terms_or_patterns:
        if term.lower() in full_text.lower():
            failure_reasons.append(f"Disallowed term '{term}' appeared in response.")

    overall_score = round(sum(m.score for m in metric_results) / len(metric_results), 2)
    passed = len(failure_reasons) == 0

    return CaseEvaluationResult(
        case_id=case.case_id,
        category=case.category,
        passed=passed,
        overall_score=overall_score,
        metrics=metric_results,
        failure_reasons=failure_reasons,
    )


class EvaluationRunner:
    """Executes evaluation suite over dataset."""

    def __init__(self, dataset: list[EvaluationTestCase] | None = None):
        self.dataset = dataset or DEFAULT_EVALUATION_DATASET

    def run_suite(
        self,
        advisor_fn: Callable[[EvaluationTestCase], dict[str, Any]],
    ) -> EvaluationSuiteReport:
        case_results: list[CaseEvaluationResult] = []
        category_scores_acc: dict[str, list[float]] = {}

        for case in self.dataset:
            try:
                resp = advisor_fn(case)
                res = evaluate_single_response(case, resp)
            except Exception as exc:
                logger.exception("Evaluation failed for case %s: %s", case.case_id, exc)
                res = CaseEvaluationResult(
                    case_id=case.case_id,
                    category=case.category,
                    passed=False,
                    overall_score=0.0,
                    metrics=[],
                    failure_reasons=[f"Execution exception: {exc}"],
                )

            case_results.append(res)
            category_scores_acc.setdefault(case.category, []).append(res.overall_score)

        passed_count = sum(1 for c in case_results if c.passed)
        total_count = len(case_results)
        acc_rate = round(passed_count / total_count, 2) if total_count > 0 else 0.0

        cat_breakdown = {
            cat: round(sum(scores) / len(scores), 2)
            for cat, scores in category_scores_acc.items()
        }

        return EvaluationSuiteReport(
            total_cases=total_count,
            passed_cases=passed_count,
            failed_cases=total_count - passed_count,
            overall_accuracy_rate=acc_rate,
            category_scores=cat_breakdown,
            case_results=case_results,
        )
