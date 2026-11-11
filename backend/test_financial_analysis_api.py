import json
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.models.goal import Goal
from app.models.risk_assessment import RiskAssessment
from app.models.document import Document

client = TestClient(app)


def test_financial_analysis_api_flow():
    db = SessionLocal()
    test_email = f"swagger_test_{uuid4().hex[:8]}@example.com"
    test_password = "Password123!"
    user = None

    try:
        # 1. Register user through API
        print(f"1. Registering user via POST /auth/register ({test_email})...")
        reg_res = client.post(
            "/auth/register",
            json={"email": test_email, "password": test_password},
        )
        assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
        user_id = reg_res.json()["id"]
        print(f"PASS: User registered with ID {user_id}")

        # 2. Login through API to get JWT Bearer token
        print("2. Authenticating via POST /auth/login...")
        login_res = client.post(
            "/auth/login",
            json={"email": test_email, "password": test_password},
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        print("PASS: Access token retrieved successfully")

        # 3. Verify unauthenticated access is rejected (401)
        print("3. Testing unauthenticated GET /financial-analysis/me...")
        unauth_res = client.get("/financial-analysis/me")
        assert unauth_res.status_code == 401, f"Expected 401, got {unauth_res.status_code}"
        print("PASS: Unauthenticated request rejected (401 Unauthorized)")

        # 4. Populate test data for this investor in the database
        print("4. Setting up profile, goals, risk assessment, and document data...")
        now = datetime.now(timezone.utc)
        profile = Profile(
            user_id=user_id,
            age=32,
            monthly_income=Decimal("150000.00"),
            monthly_expenses=Decimal("60000.00"),
            savings=Decimal("500000.00"),
            existing_investments=Decimal("1200000.00"),
            monthly_investment_capacity=Decimal("50000.00"),
        )
        goal1 = Goal(
            user_id=user_id,
            title="House Down Payment",
            goal_type="real_estate",
            target_amount=Decimal("3000000.00"),
            time_horizon_months=60,
            planned_monthly_investment=Decimal("35000.00"),
        )
        goal2 = Goal(
            user_id=user_id,
            title="Retirement Corpus",
            goal_type="retirement",
            target_amount=Decimal("20000000.00"),
            time_horizon_months=240,
            planned_monthly_investment=Decimal("40000.00"),
        )
        assessment = RiskAssessment(
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
        doc = Document(
            user_id=user_id,
            original_filename="financial_portfolio.pdf",
            stored_filename=f"{uuid4().hex}.pdf",
            content_type="application/pdf",
            file_size_bytes=15360,
            status="processed",
            indexing_status="indexed",
            indexed_at=now,
        )
        db.add_all([profile, goal1, goal2, assessment, doc])
        db.commit()
        print("PASS: Investor financial data saved to database")

        # 5. Call GET /financial-analysis/me with Bearer token
        print("5. Calling authenticated GET /financial-analysis/me...")
        res = client.get("/financial-analysis/me", headers=auth_headers)
        assert res.status_code == 200, f"Endpoint returned {res.status_code}: {res.text}"
        data = res.json()
        print("PASS: Endpoint returned 200 OK")

        # 6. Verify all expected fields in response
        assert data["user_id"] == user_id
        assert data["profile"]["age"] == 32
        assert Decimal(data["profile"]["monthly_income"]) == Decimal("150000.00")
        assert Decimal(data["profile"]["monthly_expenses"]) == Decimal("60000.00")

        assert len(data["goals"]) == 2
        assert data["risk_assessment"]["risk_score"] == 18
        assert data["risk_assessment"]["risk_category"] == "aggressive"
        assert data["risk_assessment"]["answers"] == {
            "investment_experience": 4,
            "time_horizon": 3,
            "loss_reaction": 4,
            "growth_preference": 4,
            "financial_stability": 3,
        }

        assert len(data["documents"]) == 1
        assert data["documents"][0]["filename"] == "financial_portfolio.pdf"

        # Check deterministic metrics
        metrics = data["metrics"]
        assert Decimal(metrics["monthly_surplus"]) == Decimal("90000.00")
        assert Decimal(metrics["annual_income"]) == Decimal("1800000.00")
        assert Decimal(metrics["annual_expenses"]) == Decimal("720000.00")
        assert Decimal(metrics["savings_rate_percent"]) == Decimal("60.00")
        assert Decimal(metrics["expense_ratio_percent"]) == Decimal("40.00")

        # Check goal analysis
        assert len(data["goal_analysis"]) == 2
        g1_analysis = next(g for g in data["goal_analysis"] if g["goal_title"] == "House Down Payment")
        assert Decimal(g1_analysis["required_monthly_contribution"]) == Decimal("50000.00")  # 3,000,000 / 60
        assert Decimal(g1_analysis["planned_monthly_investment"]) == Decimal("35000.00")
        assert Decimal(g1_analysis["monthly_contribution_shortfall"]) == Decimal("15000.00")  # 50,000 - 35,000

        print("\n==================================================")
        print("SUCCESS! COMPLETE FINANCIAL ANALYSIS API RESPONSE:")
        print("==================================================")
        print(json.dumps(data, indent=2))
        print("==================================================\n")

    finally:
        # Cleanup
        user = db.query(User).filter(User.email == test_email).first()
        if user:
            db.delete(user)
            db.commit()
        db.close()
        print("Test cleanup completed.")


if __name__ == "__main__":
    test_financial_analysis_api_flow()

