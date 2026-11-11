from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4
import pytest

from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.models.goal import Goal
from app.models.risk_assessment import RiskAssessment
from app.models.document import Document
from app.services.financial_context_service import (
    build_financial_context,
    FinancialContextError,
)


@pytest.fixture(scope="module")
def investor_data():
    db = SessionLocal()
    user = User(
        email=f"context_test_{uuid4().hex}@example.com",
        hashed_password="test_password_hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id

    profile = Profile(
        user_id=user_id,
        age=32,
        monthly_income=Decimal("150000.00"),
        monthly_expenses=Decimal("60000.00"),
        savings=Decimal("500000.00"),
        existing_investments=Decimal("1200000.00"),
        monthly_investment_capacity=Decimal("50000.00"),
    )
    db.add(profile)

    goal1 = Goal(
        user_id=user_id,
        title="Retirement Corpus",
        goal_type="retirement",
        target_amount=Decimal("20000000.00"),
        time_horizon_months=240,
        planned_monthly_investment=Decimal("35000.00"),
    )
    goal2 = Goal(
        user_id=user_id,
        title="House Down Payment",
        goal_type="real_estate",
        target_amount=Decimal("3000000.00"),
        time_horizon_months=48,
        planned_monthly_investment=Decimal("15000.00"),
    )
    db.add_all([goal1, goal2])

    now = datetime.now(timezone.utc)
    earlier_assessment = RiskAssessment(
        user_id=user_id,
        answers={
            "investment_experience": 2,
            "time_horizon": 2,
            "loss_reaction": 2,
            "growth_preference": 2,
            "financial_stability": 2,
        },
        risk_score=10,
        risk_category="moderate",
        assessed_at=now - timedelta(days=30),
    )
    latest_assessment = RiskAssessment(
        user_id=user_id,
        answers={
            "investment_experience": 4,
            "time_horizon": 3,
            "loss_reaction": 4,
            "growth_preference": 4,
            "financial_stability": 3,
        },
        risk_score=18,
        risk_category="aggressive",
        assessed_at=now,
    )
    db.add_all([earlier_assessment, latest_assessment])

    valid_doc = Document(
        user_id=user_id,
        original_filename="portfolio_statement.pdf",
        stored_filename=f"{uuid4().hex}.pdf",
        content_type="application/pdf",
        file_size_bytes=10240,
        status="processed",
        indexing_status="indexed",
        indexed_at=now,
    )
    pending_doc = Document(
        user_id=user_id,
        original_filename="unprocessed.pdf",
        stored_filename=f"{uuid4().hex}.pdf",
        content_type="application/pdf",
        file_size_bytes=2048,
        status="uploaded",
        indexing_status="pending",
    )
    failed_doc = Document(
        user_id=user_id,
        original_filename="failed_doc.pdf",
        stored_filename=f"{uuid4().hex}.pdf",
        content_type="application/pdf",
        file_size_bytes=4096,
        status="processed",
        indexing_status="failed",
    )
    db.add_all([valid_doc, pending_doc, failed_doc])
    db.commit()

    context = build_financial_context(db, user_id=user_id)

    yield db, user, context

    db.delete(user)
    db.commit()
    db.close()


def test_profile_information_retrieved(investor_data):
    db, user, context = investor_data
    assert context.profile is not None
    assert context.profile.age == 32
    assert context.profile.monthly_income == Decimal("150000.00")
    assert context.profile.monthly_expenses == Decimal("60000.00")
    assert context.profile.savings == Decimal("500000.00")
    assert context.profile.existing_investments == Decimal("1200000.00")
    assert context.profile.monthly_investment_capacity == Decimal("50000.00")
    print("PASS: Profile information retrieved")


def test_multiple_financial_goals_retrieved(investor_data):
    db, user, context = investor_data
    assert len(context.goals) == 2
    goal_titles = {g.title for g in context.goals}
    assert goal_titles == {"Retirement Corpus", "House Down Payment"}
    print("PASS: Multiple financial goals retrieved")


def test_latest_risk_assessment_selected(investor_data):
    db, user, context = investor_data
    assert context.risk_assessment is not None
    assert context.risk_assessment.risk_score == 18
    assert context.risk_assessment.risk_category == "aggressive"
    print("PASS: Latest risk assessment selected")


def test_only_processed_and_indexed_documents_included(investor_data):
    db, user, context = investor_data
    assert len(context.documents) == 1
    assert context.documents[0].filename == "portfolio_statement.pdf"
    assert context.documents[0].status == "processed"
    assert context.documents[0].indexing_status == "indexed"
    print("PASS: Only processed and indexed documents included")


def test_nonexistent_user_handled_correctly(investor_data):
    db, user, context = investor_data
    try:
        build_financial_context(db, user_id=999999999)
        raise AssertionError("Expected FinancialContextError for nonexistent user")
    except FinancialContextError:
        pass
    print("PASS: Nonexistent user handled correctly")


@pytest.fixture(scope="module")
def isolation_data():
    db = SessionLocal()
    user1 = User(
        email=f"context_user1_{uuid4().hex}@example.com",
        hashed_password="test_hash",
    )
    user2 = User(
        email=f"context_user2_{uuid4().hex}@example.com",
        hashed_password="test_hash",
    )
    db.add_all([user1, user2])
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    db.add(
        Profile(
            user_id=user1.id,
            age=28,
            monthly_income=Decimal("80000"),
            monthly_expenses=Decimal("40000"),
        )
    )
    db.add(
        Goal(
            user_id=user1.id,
            title="Retirement",
            goal_type="retirement",
            target_amount=Decimal("5000000"),
            time_horizon_months=120,
        )
    )
    db.commit()

    context1 = build_financial_context(db, user_id=user1.id)
    context2 = build_financial_context(db, user_id=user2.id)

    yield db, user1, user2, context1, context2

    db.delete(user1)
    db.delete(user2)
    db.commit()
    db.close()


def test_missing_profile_handled_correctly(isolation_data):
    db, user1, user2, context1, context2 = isolation_data
    assert context2.profile is None
    print("PASS: Missing profile handled correctly")


def test_empty_financial_data_handled_correctly(isolation_data):
    db, user1, user2, context1, context2 = isolation_data
    assert context2.goals == []
    assert context2.risk_assessment is None
    assert context2.documents == []
    print("PASS: Empty financial data handled correctly")


def test_user_data_isolation_verified(isolation_data):
    db, user1, user2, context1, context2 = isolation_data
    assert context1.profile is not None
    assert context1.profile.age == 28
    assert len(context1.goals) == 1
    assert context1.goals[0].title == "Retirement"

    assert context2.profile is None
    assert len(context2.goals) == 0
    print("PASS: User data isolation verified")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
