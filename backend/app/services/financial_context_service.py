
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.schemas.financial_context import (
    FinancialContext,
    InvestorProfileContext,
    InvestorGoalContext,
    InvestorRiskContext,
    InvestorDocumentContext,
    FinancialMetricsContext,
    FinancialGoalAnalysis,
    RiskCategory,
    RiskAnswers,
)
from app.services.financial_calculation_service import (
    calculate_monthly_surplus,
    calculate_annual_income,
    calculate_annual_expenses,
    calculate_savings_rate,
    calculate_expense_ratio,
    calculate_required_monthly_contribution,
)


class FinancialContextError(Exception):
    """Raised when financial context cannot be constructed."""


def calculate_investor_metrics(profile) -> FinancialMetricsContext:
    """
    Calculate financial metrics from available profile data.
    Missing information is represented as None.
    No financial values are assumed or invented.
    """
    if profile is None:
        return FinancialMetricsContext()

    income = profile.monthly_income
    expenses = profile.monthly_expenses
    metrics = FinancialMetricsContext()

    if income is not None:
        metrics.annual_income = calculate_annual_income(income)

    if expenses is not None:
        metrics.annual_expenses = calculate_annual_expenses(expenses)

    if income is not None and expenses is not None:
        metrics.monthly_surplus = calculate_monthly_surplus(
            income,
            expenses,
        )
        metrics.savings_rate_percent = calculate_savings_rate(
            income,
            expenses,
        )
        metrics.expense_ratio_percent = calculate_expense_ratio(
            income,
            expenses,
        )

    return metrics


def calculate_goal_analyses(goals) -> list[FinancialGoalAnalysis]:
    """
    Calculate required monthly contributions and shortfalls for investor goals.
    """
    analyses: list[FinancialGoalAnalysis] = []
    for goal in goals:
        required = calculate_required_monthly_contribution(
            goal.target_amount,
            goal.time_horizon_months,
        )
        shortfall = None
        if goal.planned_monthly_investment is not None:
            shortfall = max(
                Decimal("0.00"),
                (required - Decimal(str(goal.planned_monthly_investment))).quantize(
                    Decimal("0.01")
                ),
            )

        analyses.append(
            FinancialGoalAnalysis(
                goal_id=goal.id,
                goal_title=goal.title,
                required_monthly_contribution=required,
                planned_monthly_investment=goal.planned_monthly_investment,
                monthly_contribution_shortfall=shortfall,
            )
        )
    return analyses


def build_financial_context(
    db: Session,
    user_id: int,
) -> FinancialContext:
    """
    Build a unified financial context for an investor.

    Only data belonging to the requested user is retrieved.
    Only successfully processed and indexed documents are included.
    """

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    statement = (
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.goals),
            selectinload(User.risk_assessments),
            selectinload(User.documents),
        )
        .where(User.id == user_id)
    )

    try:
        user = db.scalars(statement).unique().first()
    except Exception as exc:
        raise FinancialContextError(
            "Unable to retrieve investor information."
        ) from exc

    if user is None:
        raise FinancialContextError("Investor not found.")

    # 1. Profile information
    profile_context = None

    if user.profile is not None:
        profile_context = InvestorProfileContext(
            age=user.profile.age,
            monthly_income=user.profile.monthly_income,
            monthly_expenses=user.profile.monthly_expenses,
            savings=user.profile.savings,
            existing_investments=user.profile.existing_investments,
            monthly_investment_capacity=(
                user.profile.monthly_investment_capacity
            ),
        )

    # 2. Financial goals
    goals_context = [
        InvestorGoalContext(
            id=goal.id,
            title=goal.title,
            goal_type=goal.goal_type,
            target_amount=goal.target_amount,
            time_horizon_months=goal.time_horizon_months,
            planned_monthly_investment=(
                goal.planned_monthly_investment
            ),
        )
        for goal in user.goals
    ]

    # 3. Latest risk assessment
    latest_assessment = max(
        user.risk_assessments,
        key=lambda assessment: (
            assessment.assessed_at,
            assessment.id,
        ),
        default=None,
    )

    risk_context = None

    if latest_assessment is not None:
        risk_category = TypeAdapter(RiskCategory).validate_python(
            latest_assessment.risk_category
        )
        risk_answers = TypeAdapter(RiskAnswers).validate_python(
            latest_assessment.answers
        )
        risk_context = InvestorRiskContext(
            risk_score=latest_assessment.risk_score,
            risk_category=risk_category,
            answers=risk_answers,
            assessed_at=latest_assessment.assessed_at,
        )

    # 4. Successfully processed and indexed documents
    documents_context = [
        InvestorDocumentContext(
            id=document.id,
            filename=document.original_filename,
            status=document.status,
            indexing_status=document.indexing_status,
            indexed_at=document.indexed_at,
        )
        for document in user.documents
        if (
            document.status == "processed"
            and document.indexing_status == "indexed"
        )
    ]

    metrics = calculate_investor_metrics(user.profile)
    goal_analyses = calculate_goal_analyses(user.goals)

    return FinancialContext(
        user_id=user.id,
        profile=profile_context,
        goals=goals_context,
        risk_assessment=risk_context,
        documents=documents_context,
        metrics=metrics,
        goal_analysis=goal_analyses,
        generated_at=datetime.now(timezone.utc),
    )
