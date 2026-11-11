from decimal import Decimal
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.models.goal import Goal
from app.services.financial_context_service import build_financial_context


def test_financial_context_includes_calculated_metrics():
    db = SessionLocal()
    user = None
    try:
        user = User(
            email=f"metrics_{uuid4().hex}@example.com",
            hashed_password="test_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = Profile(
            user_id=user.id,
            age=30,
            monthly_income=Decimal("100000"),
            monthly_expenses=Decimal("60000"),
            savings=Decimal("500000"),
            existing_investments=Decimal("200000"),
            monthly_investment_capacity=Decimal("30000"),
        )
        goal = Goal(
            user_id=user.id,
            title="House Down Payment",
            goal_type="real_estate",
            target_amount=Decimal("1200000"),
            time_horizon_months=60,
            planned_monthly_investment=Decimal("15000"),
        )
        db.add_all([profile, goal])
        db.commit()

        context = build_financial_context(db, user_id=user.id)

        # Cash flow and ratios
        assert context.metrics.monthly_surplus == Decimal("40000.00")
        assert context.metrics.annual_income == Decimal("1200000.00")
        assert context.metrics.annual_expenses == Decimal("720000.00")
        assert context.metrics.savings_rate_percent == Decimal("40.00")
        assert context.metrics.expense_ratio_percent == Decimal("60.00")

        # Goal analysis
        assert len(context.goal_analysis) == 1
        analysis = context.goal_analysis[0]
        assert analysis.goal_id == goal.id
        assert analysis.goal_title == "House Down Payment"
        assert analysis.required_monthly_contribution == Decimal("20000.00")
        assert analysis.planned_monthly_investment == Decimal("15000.00")
        assert analysis.monthly_contribution_shortfall == Decimal("5000.00")
        print("PASS: Financial context metrics and goal analysis calculated correctly")

    finally:
        if user is not None and user.id is not None:
            db.delete(user)
            db.commit()
        db.close()


def test_financial_context_calculation_with_missing_financial_data():
    db = SessionLocal()
    user = None
    try:
        user = User(
            email=f"metrics_empty_{uuid4().hex}@example.com",
            hashed_password="test_hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        context = build_financial_context(db, user_id=user.id)

        assert context.metrics.monthly_surplus is None
        assert context.metrics.annual_income is None
        assert context.metrics.annual_expenses is None
        assert context.metrics.savings_rate_percent is None
        assert context.metrics.expense_ratio_percent is None
        assert context.goal_analysis == []
        print("PASS: Missing financial data gracefully results in None metrics and empty goal analysis")

    finally:
        if user is not None and user.id is not None:
            db.delete(user)
            db.commit()
        db.close()


if __name__ == "__main__":
    test_financial_context_includes_calculated_metrics()
    test_financial_context_calculation_with_missing_financial_data()

