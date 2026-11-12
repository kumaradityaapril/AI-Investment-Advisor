from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.analysis_history import AnalysisHistory
from app.models.user import User
from app.schemas.ai_advisor import (
    ADVISOR_DISCLAIMER,
    AIAdvisorResponse,
    AdvisorEvidence,
    AdvisorRecommendation,
)
from app.schemas.financial_context import (
    FinancialContext,
    FinancialMetricsContext,
)
from app.services.analysis_history_service import (
    delete_user_analysis,
    get_user_analysis_by_id,
    list_user_analyses,
    save_analysis_history,
)

client = TestClient(app)


def make_sample_response() -> AIAdvisorResponse:
    return AIAdvisorResponse(
        overall_assessment="Overall financial health is solid with strong cash flow.",
        key_findings=["Savings rate exceeds 40%."],
        recommendations=[
            AdvisorRecommendation(
                title="Increase Equity Allocation",
                explanation="Horizon allows for equity compounding.",
                suggested_action="Allocate 20% to index funds.",
                priority="high",
            )
        ],
        risk_considerations=["Short-term market volatility."],
        assumptions=["Income remains stable."],
        limitations=["Tax optimization not included."],
        evidence=[
            AdvisorEvidence(
                chunk_id=1,
                document_id=10,
                filename="portfolio.pdf",
                page_number=2,
                supporting_excerpt="Equity holdings grew 15%.",
            )
        ],
        disclaimer=ADVISOR_DISCLAIMER,
    )


def make_sample_context(user_id: int) -> FinancialContext:
    return FinancialContext(
        user_id=user_id,
        metrics=FinancialMetricsContext(
            monthly_surplus=Decimal("40000.00"),
            annual_income=Decimal("1200000.00"),
            annual_expenses=Decimal("720000.00"),
            savings_rate_percent=Decimal("40.00"),
            expense_ratio_percent=Decimal("60.00"),
        ),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def test_users():
    db = SessionLocal()
    u1 = User(
        email=f"history_u1_{uuid4().hex[:6]}@example.com",
        hashed_password="pw1",
    )
    u2 = User(
        email=f"history_u2_{uuid4().hex[:6]}@example.com",
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


def test_save_and_retrieve_analysis_history(test_users):
    user1_id, _ = test_users
    db = SessionLocal()
    try:
        response = make_sample_response()
        context = make_sample_context(user1_id)
        question = "How should I allocate my ₹40,000 monthly surplus?"

        saved = save_analysis_history(
            db=db,
            user_id=user1_id,
            question=question,
            response=response,
            financial_context=context,
        )

        assert saved.id is not None
        assert saved.user_id == user1_id
        assert saved.question == question
        assert saved.financial_context_snapshot["metrics"]["monthly_surplus"] == "40000.00"
        assert saved.advisor_response_snapshot["overall_assessment"].startswith("Overall financial health")
        assert len(saved.evidence_references) == 1
        assert saved.evidence_references[0]["filename"] == "portfolio.pdf"

        # Fetch by ID
        fetched = get_user_analysis_by_id(db, user_id=user1_id, analysis_id=saved.id)
        assert fetched is not None
        assert fetched.id == saved.id

    finally:
        db.close()


def test_list_analyses_and_pagination(test_users):
    user1_id, _ = test_users
    db = SessionLocal()
    try:
        response = make_sample_response()
        context = make_sample_context(user1_id)

        for i in range(3):
            save_analysis_history(
                db=db,
                user_id=user1_id,
                question=f"Question {i}",
                response=response,
                financial_context=context,
            )

        items, total = list_user_analyses(db, user_id=user1_id, skip=0, limit=2)
        assert total >= 3
        assert len(items) == 2
        assert items[0].overall_assessment.startswith("Overall financial health")
        assert items[0].recommendations_count == 1

    finally:
        db.close()


def test_cross_user_isolation_enforced(test_users):
    user1_id, user2_id = test_users
    db = SessionLocal()
    try:
        response = make_sample_response()
        context = make_sample_context(user1_id)

        saved = save_analysis_history(
            db=db,
            user_id=user1_id,
            question="User 1 private inquiry",
            response=response,
            financial_context=context,
        )

        # User 2 cannot fetch User 1's analysis
        cross_fetch = get_user_analysis_by_id(db, user_id=user2_id, analysis_id=saved.id)
        assert cross_fetch is None

        # User 2 cannot delete User 1's analysis
        cross_delete = delete_user_analysis(db, user_id=user2_id, analysis_id=saved.id)
        assert cross_delete is False

        # Analysis still exists for User 1
        assert get_user_analysis_by_id(db, user_id=user1_id, analysis_id=saved.id) is not None

    finally:
        db.close()


def test_delete_user_analysis_success(test_users):
    user1_id, _ = test_users
    db = SessionLocal()
    try:
        response = make_sample_response()
        context = make_sample_context(user1_id)

        saved = save_analysis_history(
            db=db,
            user_id=user1_id,
            question="To be deleted",
            response=response,
            financial_context=context,
        )

        deleted = delete_user_analysis(db, user_id=user1_id, analysis_id=saved.id)
        assert deleted is True

        # Now should not exist
        assert get_user_analysis_by_id(db, user_id=user1_id, analysis_id=saved.id) is None

    finally:
        db.close()


def test_advisor_history_api_endpoints(test_users):
    user1_id, _ = test_users
    db = SessionLocal()
    user1 = db.get(User, user1_id)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user1

    try:
        # Pre-seed one record
        response = make_sample_response()
        context = make_sample_context(user1_id)
        saved = save_analysis_history(
            db=db,
            user_id=user1_id,
            question="API test question",
            response=response,
            financial_context=context,
        )

        # 1. GET /advisor/history
        res_list = client.get("/advisor/history?skip=0&limit=10")
        assert res_list.status_code == 200
        data = res_list.json()
        assert data["total"] >= 1
        assert any(item["id"] == saved.id for item in data["items"])

        # 2. GET /advisor/history/{id}
        res_detail = client.get(f"/advisor/history/{saved.id}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert detail["id"] == saved.id
        assert detail["question"] == "API test question"
        assert "metrics" in detail["financial_context_snapshot"]

        # 3. GET nonexistent returns 404
        res_404 = client.get("/advisor/history/999999")
        assert res_404.status_code == 404

        # 4. DELETE /advisor/history/{id}
        res_del = client.delete(f"/advisor/history/{saved.id}")
        assert res_del.status_code == 200
        assert res_del.json()["detail"] == "Analysis deleted successfully."

        # Verify deletion
        res_after = client.get(f"/advisor/history/{saved.id}")
        assert res_after.status_code == 404

    finally:
        app.dependency_overrides.clear()
        db.close()

