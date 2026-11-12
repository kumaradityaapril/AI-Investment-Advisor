from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.goal import Goal
from app.models.profile import Profile
from app.models.user import User
from app.schemas.scenario_simulation import (
    SCENARIO_DISCLAIMER,
    BaseFinancialOverrides,
    ScenarioAIExplanation,
    ScenarioParameterChanges,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
)
from app.services.scenario_simulator_service import (
    ScenarioSimulationError,
    _validate_scenario_safety,
    calculate_scenario_trajectory,
    run_scenario_simulation,
)

client = TestClient(app)


@pytest.fixture
def test_users():
    db = SessionLocal()
    u1 = User(
        email=f"scenario_u1_{uuid4().hex[:6]}@example.com",
        hashed_password="pw1",
    )
    db.add(u1)
    db.commit()
    db.refresh(u1)
    user1_id = u1.id
    db.close()

    yield user1_id

    clean_db = SessionLocal()
    try:
        user1 = clean_db.get(User, user1_id)
        if user1:
            clean_db.delete(user1)
        clean_db.commit()
    finally:
        clean_db.close()


@pytest.fixture
def mock_scenario_explanation():
    return ScenarioAIExplanation(
        summary_narrative="Increasing your monthly SIP by ₹5,000 creates substantial long-term wealth over a 10-year horizon.",
        key_advantages=[
            "Additional corpus growth due to compounding on incremental contributions.",
            "Accelerates progress toward long-term wealth creation.",
        ],
        trade_offs_and_risks=[
            "Reduces monthly discretionary cash buffer by ₹5,000.",
            "Equity markets experience intermittent volatility; equity returns fluctuate.",
        ],
        goal_impact_analysis="Significantly reduces the remaining shortfall for your target goals.",
        practical_next_steps=[
            "Review your monthly budget to ensure ₹5,000 surplus is consistent.",
            "Set up an automated ECS mandate for the new SIP amount.",
        ],
        assumptions_disclaimer=SCENARIO_DISCLAIMER,
    )


# -------------------------------------------------------------
# 1. Deterministic Calculation Tests
# -------------------------------------------------------------

def test_calculate_scenario_trajectory_sip_step_up():
    params = ScenarioParameterChanges(
        delta_monthly_investment=Decimal("5000"),
        assumed_annual_return_percent=Decimal("12.0"),
        time_horizon_years=10,
    )
    comparison, trajectory = calculate_scenario_trajectory(
        baseline_income=Decimal("80000"),
        baseline_expenses=Decimal("50000"),
        baseline_sip=Decimal("10000"),
        existing_corpus=Decimal("50000"),
        params=params,
    )

    assert len(trajectory) == 10
    assert trajectory[0].year == 1
    assert trajectory[9].year == 10

    # Year 10 scenario should exceed baseline
    final_point = trajectory[-1]
    assert final_point.scenario_projected_corpus > final_point.baseline_projected_corpus
    assert final_point.delta_corpus > Decimal("0")

    # Additional out of pocket over 10 years (120 months) for +₹5k/mo is exactly ₹6,00,000
    assert comparison.additional_out_of_pocket_invested == Decimal("600000.00")
    # Compounding produces more than the invested capital
    assert comparison.absolute_growth_delta > comparison.additional_out_of_pocket_invested
    assert comparison.net_wealth_gain_from_change > Decimal("0")
    assert comparison.wealth_multiplier_on_new_capital is not None
    assert comparison.wealth_multiplier_on_new_capital > Decimal("1.5")


def test_calculate_scenario_trajectory_zero_return():
    params = ScenarioParameterChanges(
        delta_monthly_investment=Decimal("2000"),
        assumed_annual_return_percent=Decimal("0.0"),
        time_horizon_years=2,
    )
    comparison, trajectory = calculate_scenario_trajectory(
        baseline_income=Decimal("50000"),
        baseline_expenses=Decimal("30000"),
        baseline_sip=Decimal("5000"),
        existing_corpus=Decimal("10000"),
        params=params,
    )

    assert len(trajectory) == 2
    final = trajectory[-1]
    # At 0%, baseline corpus = 10,000 + (5000 * 24) = 1,30,000
    assert final.baseline_projected_corpus == Decimal("130000.00")
    # Scenario corpus = 10,000 + (7000 * 24) = 1,78,000
    assert final.scenario_projected_corpus == Decimal("178000.00")
    assert comparison.absolute_growth_delta == Decimal("48000.00")
    assert comparison.net_wealth_gain_from_change == Decimal("0.00")


def test_calculate_scenario_with_goal():
    goal = Goal(
        id=99,
        user_id=1,
        title="House Downpayment",
        goal_type="real_estate",
        target_amount=Decimal("5000000"),
        time_horizon_months=120,
    )
    params = ScenarioParameterChanges(
        delta_monthly_investment=Decimal("10000"),
        assumed_annual_return_percent=Decimal("12.0"),
        time_horizon_years=10,
        target_goal_id=99,
    )
    comparison, trajectory = calculate_scenario_trajectory(
        baseline_income=Decimal("100000"),
        baseline_expenses=Decimal("60000"),
        baseline_sip=Decimal("15000"),
        existing_corpus=Decimal("200000"),
        params=params,
        target_goal=goal,
    )

    assert comparison.goal_id == 99
    assert comparison.goal_title == "House Downpayment"
    assert comparison.scenario_goal_shortfall is not None
    assert comparison.goal_shortfall_reduction is not None
    assert comparison.goal_shortfall_reduction > Decimal("0")


# -------------------------------------------------------------
# 2. Safety Validation Tests
# -------------------------------------------------------------

def test_scenario_safety_rejects_guaranteed_returns(mock_scenario_explanation):
    mock_scenario_explanation.summary_narrative = "We offer guaranteed returns of 18% with zero risk."
    with pytest.raises(ScenarioSimulationError, match="disallowed certainty"):
        _validate_scenario_safety(mock_scenario_explanation)


def test_scenario_safety_allows_negated_warnings(mock_scenario_explanation):
    mock_scenario_explanation.summary_narrative = (
        "Market returns are not guaranteed, and past performance is no assurance of future gains."
    )
    _validate_scenario_safety(mock_scenario_explanation)


# -------------------------------------------------------------
# 3. Service & API Endpoint Tests
# -------------------------------------------------------------

def test_run_scenario_simulation_service(test_users, mock_scenario_explanation, monkeypatch):
    user1_id = test_users
    db = SessionLocal()
    try:
        # Pre-seed profile
        p = Profile(
            user_id=user1_id,
            monthly_income=Decimal("90000.00"),
            monthly_expenses=Decimal("50000.00"),
            savings=Decimal("100000.00"),
            existing_investments=Decimal("50000.00"),
        )
        db.add(p)
        db.commit()

        monkeypatch.setattr(
            "app.services.scenario_simulator_service.generate_scenario_explanation",
            lambda **kwargs: mock_scenario_explanation,
        )

        resp = run_scenario_simulation(
            db=db,
            user_id=user1_id,
            request=ScenarioSimulationRequest(
                scenario_name="Boost SIP by 5k",
                parameters=ScenarioParameterChanges(
                    delta_monthly_investment=Decimal("5000"),
                    assumed_annual_return_percent=Decimal("12.0"),
                    time_horizon_years=5,
                ),
            ),
        )

        assert resp.scenario_name == "Boost SIP by 5k"
        assert len(resp.yearly_trajectory) == 5
        assert resp.comparison.scenario_monthly_investment > resp.comparison.baseline_monthly_investment
        assert resp.ai_explanation.summary_narrative == mock_scenario_explanation.summary_narrative

    finally:
        db.close()


def test_scenario_templates_api():
    res = client.get("/scenarios/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 5
    assert any(t["template_id"] == "sip_step_up_5k" for t in templates)


def test_scenario_simulate_api(test_users, mock_scenario_explanation, monkeypatch):
    user1_id = test_users
    db = SessionLocal()
    user1 = db.get(User, user1_id)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user1

    try:
        monkeypatch.setattr(
            "app.services.scenario_simulator_service.generate_scenario_explanation",
            lambda **kwargs: mock_scenario_explanation,
        )

        res = client.post(
            "/scenarios/simulate",
            json={
                "scenario_name": "API Test Scenario",
                "parameters": {
                    "delta_monthly_investment": 5000,
                    "assumed_annual_return_percent": 11.5,
                    "time_horizon_years": 8,
                },
                "base_overrides": {
                    "monthly_income": 85000,
                    "monthly_expenses": 45000,
                    "current_monthly_investment": 15000,
                    "existing_accumulated_corpus": 50000,
                },
            },
        )

        assert res.status_code == 200
        data = res.json()
        assert data["scenario_name"] == "API Test Scenario"
        assert len(data["yearly_trajectory"]) == 8
        assert Decimal(str(data["comparison"]["baseline_monthly_investment"])) == Decimal("15000.00")
        assert Decimal(str(data["comparison"]["scenario_monthly_investment"])) == Decimal("20000.00")
        assert "ai_explanation" in data

    finally:
        app.dependency_overrides.clear()
        db.close()


def test_scenario_simulate_api_unauthorized():
    res = client.post(
        "/scenarios/simulate",
        json={
            "scenario_name": "Test",
            "parameters": {"delta_monthly_investment": 5000},
        },
    )
    assert res.status_code == 401
