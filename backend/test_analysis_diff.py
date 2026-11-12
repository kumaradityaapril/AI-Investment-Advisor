from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.user import User
from app.models.analysis_history import AnalysisHistory
from app.schemas.analysis_diff import (
    AnalysisDiffExplanation,
    AnalysisDiffRequest,
    AnalysisDiffResponse,
)
from app.services.analysis_diff_service import (
    AnalysisDiffError,
    _validate_diff_explanation_safety,
    calculate_goal_deltas,
    calculate_metric_deltas,
    calculate_risk_shift,
    compute_analysis_diff,
)

client = TestClient(app)


@pytest.fixture
def test_users():
    db = SessionLocal()
    u1 = User(
        email=f"diff_u1_{uuid4().hex[:6]}@example.com",
        hashed_password="pw1",
    )
    u2 = User(
        email=f"diff_u2_{uuid4().hex[:6]}@example.com",
        hashed_password="pw2",
    )
    db.add_all([u1, u2])
    db.commit()
    db.refresh(u1)
    db.refresh(u2)
    user1_id = u1.id
    user2_id = u2.id
    db.close()

    yield user1_id, user2_id

    clean_db = SessionLocal()
    try:
        user1 = clean_db.get(User, user1_id)
        user2 = clean_db.get(User, user2_id)
        if user1:
            clean_db.delete(user1)
        if user2:
            clean_db.delete(user2)
        clean_db.commit()
    finally:
        clean_db.close()


@pytest.fixture
def mock_diff_explanation():
    return AnalysisDiffExplanation(
        summary_narrative="Over the elapsed 30 days, your financial standing improved with a higher savings rate and reduced expenses.",
        key_improvements=[
            "Monthly surplus grew by ₹10,000.",
            "Savings rate rose by 10% due to disciplined expense management.",
        ],
        key_concerns=[
            "Retirement goal still faces a remaining shortfall.",
        ],
        stale_recommendations=[
            "Emergency fund recommendation is now fulfilled due to recent savings additions.",
        ],
        updated_strategic_focus=[
            "Prioritize stepping up equity index fund SIPs for the retirement goal.",
        ],
    )


def test_calculate_metric_deltas_improved_and_declined():
    baseline_ctx = {
        "profile": {"monthly_income": 100000, "monthly_expenses": 60000},
        "metrics": {
            "monthly_surplus": 40000,
            "savings_rate_percent": 40.0,
            "expense_ratio_percent": 60.0,
        },
    }
    current_ctx = {
        "profile": {"monthly_income": 110000, "monthly_expenses": 55000},
        "metrics": {
            "monthly_surplus": 55000,
            "savings_rate_percent": 50.0,
            "expense_ratio_percent": 50.0,
        },
    }

    deltas = calculate_metric_deltas(baseline_ctx, current_ctx)
    by_key = {d.metric_key: d for d in deltas}

    assert by_key["monthly_income"].delta_value == Decimal("10000")
    assert by_key["monthly_income"].trend == "improved"

    assert by_key["monthly_expenses"].delta_value == Decimal("-5000")
    assert by_key["monthly_expenses"].trend == "improved"  # lower expenses is better

    assert by_key["monthly_surplus"].delta_value == Decimal("15000")
    assert by_key["monthly_surplus"].trend == "improved"

    assert by_key["expense_ratio_percent"].delta_value == Decimal("-10.0")
    assert by_key["expense_ratio_percent"].trend == "improved"


def test_calculate_risk_shift():
    baseline_ctx = {
        "risk_assessment": {
            "risk_category": "Conservative",
            "risk_score": 3,
        }
    }
    current_ctx = {
        "risk_assessment": {
            "risk_category": "Moderate",
            "risk_score": 6,
        }
    }

    shift = calculate_risk_shift(baseline_ctx, current_ctx)
    assert shift.baseline_category == "Conservative"
    assert shift.current_category == "Moderate"
    assert shift.score_delta == 3
    assert shift.category_changed is True


def test_calculate_goal_deltas():
    baseline_ctx = {
        "goal_analysis": [
            {
                "goal_id": 1,
                "goal_title": "Retirement",
                "target_amount": 10000000,
                "monthly_contribution_shortfall": 25000,
            },
            {
                "goal_id": 2,
                "goal_title": "Old Car",
                "target_amount": 500000,
                "monthly_contribution_shortfall": 10000,
            },
        ]
    }
    current_ctx = {
        "goal_analysis": [
            {
                "goal_id": 1,
                "goal_title": "Retirement",
                "target_amount": 10000000,
                "monthly_contribution_shortfall": 15000,
            },
            {
                "goal_id": 3,
                "goal_title": "House Downpayment",
                "target_amount": 2000000,
                "monthly_contribution_shortfall": 30000,
            },
        ]
    }

    deltas = calculate_goal_deltas(baseline_ctx, current_ctx)
    by_id = {d.goal_id: d for d in deltas}

    assert by_id[1].status == "modified"
    assert by_id[1].shortfall_delta == Decimal("-10000")  # shortfall reduced by 10k
    assert by_id[2].status == "removed"
    assert by_id[3].status == "new"


def test_diff_explanation_safety_rejection():
    unsafe_explanation = AnalysisDiffExplanation(
        summary_narrative="We offer guaranteed returns of 15% with zero-risk investment.",
        key_improvements=["Income increased by ₹10,000."],
        key_concerns=["None"],
        stale_recommendations=["Old savings rule is no longer applicable."],
        updated_strategic_focus=["Save more."],
    )
    with pytest.raises(AnalysisDiffError, match="disallowed certainty"):
        _validate_diff_explanation_safety(unsafe_explanation)


def test_compute_analysis_diff_service(test_users, mock_diff_explanation):
    user1_id, _ = test_users
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        t1 = now - timedelta(days=30)
        t2 = now

        h1 = AnalysisHistory(
            user_id=user1_id,
            question="Initial analysis",
            advisor_model="test-gemini",
            financial_context_snapshot={
                "profile": {"monthly_income": 80000, "monthly_expenses": 50000},
                "metrics": {"monthly_surplus": 30000},
            },
            advisor_response_snapshot={
                "recommendations": [{"title": "Old Emergency Rec", "suggested_action": "Save 5k"}]
            },
            created_at=t1,
        )
        h2 = AnalysisHistory(
            user_id=user1_id,
            question="Updated analysis",
            advisor_model="test-gemini",
            financial_context_snapshot={
                "profile": {"monthly_income": 95000, "monthly_expenses": 50000},
                "metrics": {"monthly_surplus": 45000},
            },
            advisor_response_snapshot={
                "recommendations": [{"title": "New Equity Rec", "suggested_action": "Invest 15k"}]
            },
            created_at=t2,
        )
        db.add_all([h1, h2])
        db.commit()
        db.refresh(h1)
        db.refresh(h2)

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.parsed = mock_diff_explanation
        mock_client.models.generate_content.return_value = mock_resp

        # Reverse order passed -> verifies chronological sorting
        diff = compute_analysis_diff(
            db=db,
            user_id=user1_id,
            request=AnalysisDiffRequest(
                baseline_analysis_id=h2.id,
                current_analysis_id=h1.id,
            ),
            client=mock_client,
        )

        assert diff.baseline_analysis_id == h1.id
        assert diff.current_analysis_id == h2.id
        assert diff.elapsed_days == 30
        assert len(diff.metric_deltas) > 0
        surplus_delta = next(d for d in diff.metric_deltas if d.metric_key == "monthly_surplus")
        assert surplus_delta.delta_value == Decimal("15000")
        assert diff.ai_explanation.stale_recommendations == [
            "Emergency fund recommendation is now fulfilled due to recent savings additions."
        ]
    finally:
        db.close()


def test_analysis_diff_api_endpoint(test_users, mock_diff_explanation, monkeypatch):
    user1_id, _ = test_users
    db = SessionLocal()
    user1 = db.get(User, user1_id)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user1

    try:
        now = datetime.now(timezone.utc)
        h1 = AnalysisHistory(
            user_id=user1_id,
            question="Baseline query",
            advisor_model="gemini",
            financial_context_snapshot={"metrics": {"monthly_surplus": 20000}},
            advisor_response_snapshot={"recommendations": []},
            created_at=now - timedelta(days=15),
        )
        h2 = AnalysisHistory(
            user_id=user1_id,
            question="Current query",
            advisor_model="gemini",
            financial_context_snapshot={"metrics": {"monthly_surplus": 30000}},
            advisor_response_snapshot={"recommendations": []},
            created_at=now,
        )
        db.add_all([h1, h2])
        db.commit()
        db.refresh(h1)
        db.refresh(h2)

        monkeypatch.setattr(
            "app.services.analysis_diff_service.generate_diff_explanation",
            lambda **kwargs: mock_diff_explanation,
        )

        resp = client.post(
            "/advisor/history/diff",
            json={
                "baseline_analysis_id": h1.id,
                "current_analysis_id": h2.id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["baseline_analysis_id"] == h1.id
        assert data["current_analysis_id"] == h2.id
        assert data["elapsed_days"] == 15
        assert "ai_explanation" in data
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_analysis_diff_api_cross_user_isolation(test_users):
    user1_id, user2_id = test_users
    db = SessionLocal()
    user1 = db.get(User, user1_id)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user1

    try:
        now = datetime.now(timezone.utc)
        h_other = AnalysisHistory(
            user_id=user2_id,
            question="Other query",
            advisor_model="gemini",
            financial_context_snapshot={},
            advisor_response_snapshot={},
            created_at=now,
        )
        h_me = AnalysisHistory(
            user_id=user1_id,
            question="My query",
            advisor_model="gemini",
            financial_context_snapshot={},
            advisor_response_snapshot={},
            created_at=now,
        )
        db.add_all([h_other, h_me])
        db.commit()
        db.refresh(h_other)
        db.refresh(h_me)

        resp = client.post(
            "/advisor/history/diff",
            json={
                "baseline_analysis_id": h_other.id,
                "current_analysis_id": h_me.id,
            },
        )
        assert resp.status_code == 404
        assert f"Baseline analysis {h_other.id} not found" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        db.close()
