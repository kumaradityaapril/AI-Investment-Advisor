from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import User
from app.api.auth import get_current_user
from app.schemas.investment_comparison import (
    COMPARISON_DISCLAIMER,
    InvestmentComparisonExplanation,
    InvestmentComparisonItem,
    InvestmentComparisonRequest,
    InvestmentComparisonResponse,
    InvestmentOptionInput,
    OptionSuitability,
)
from app.services.investment_comparison_service import (
    InvestmentComparisonError,
    build_comparison_prompt,
    compare_investments,
    compute_comparison_items,
)


def sample_options():
    return [
        InvestmentOptionInput(
            name="Bank Fixed Deposit",
            category="fixed_income",
            expected_annual_return_percent=Decimal("7.0"),
            risk_level="low",
            liquidity="moderate",
            lock_in_period_months=12,
            recommended_horizon_months=12,
            tax_implications="Interest is taxed according to income slab rate.",
            capital_protection="Insured by DICGC up to INR 5 lakh per bank.",
            advantages=["Predictable returns", "High capital safety"],
            disadvantages=["May not beat inflation after tax", "Premature penalty"],
        ),
        InvestmentOptionInput(
            name="Nifty 50 Index Fund",
            category="equity_mutual_fund",
            expected_annual_return_percent=Decimal("12.0"),
            risk_level="high",
            liquidity="high",
            lock_in_period_months=0,
            recommended_horizon_months=60,
            tax_implications="LTCG at 12.5% beyond 1.25 lakh/year.",
            capital_protection="Market-linked, not guaranteed.",
            advantages=["High long-term growth potential", "Low expense ratio"],
            disadvantages=["Short-term volatility", "Capital can decline in downturns"],
        ),
    ]


def mock_explanation():
    return InvestmentComparisonExplanation(
        summary="Fixed Deposit offers predictable capital protection while Nifty 50 offers equity growth potential.",
        key_differences=[
            "Fixed Deposit guarantees contractual nominal return, whereas Nifty 50 is market-linked.",
            "Nifty 50 is better suited for long-term horizons of 5+ years due to equity volatility.",
        ],
        suitability_analysis=[
            OptionSuitability(
                option_name="Bank Fixed Deposit",
                suitable_for="Conservative investors or emergency funds requiring capital preservation.",
                unsuitable_for="Long-term wealth creation exceeding inflation.",
                key_tradeoff="Sacrifices higher inflation-adjusted growth for nominal capital safety.",
            ),
            OptionSuitability(
                option_name="Nifty 50 Index Fund",
                suitable_for="Investors with 5+ year horizons willing to tolerate periodic volatility.",
                unsuitable_for="Short-term goals under 3 years.",
                key_tradeoff="Accepts short-term price fluctuations for long-term compounding.",
            ),
        ],
        risk_tradeoffs=[
            "Fixed deposits face inflation erosion risk.",
            "Equity index funds face market drawdowns.",
        ],
        assumptions_and_missing_info=[
            "Assumes constant annual return rates over the period.",
        ],
    )


def test_comparison_schema_requires_at_least_two_options():
    with pytest.raises(ValueError):
        InvestmentComparisonRequest(options=[sample_options()[0]])


def test_comparison_schema_rejects_duplicate_names():
    opt = sample_options()[0]
    opt_duplicate = opt.model_copy()
    with pytest.raises(ValueError, match="unique names"):
        InvestmentComparisonRequest(options=[opt, opt_duplicate])


def test_comparison_schema_enforces_paired_amount_and_horizon():
    # Amount without horizon
    with pytest.raises(ValueError, match="time_horizon_months is required"):
        InvestmentComparisonRequest(
            options=sample_options(),
            investment_amount=Decimal("100000"),
        )

    # Horizon without amount
    with pytest.raises(ValueError, match="investment_amount is required"):
        InvestmentComparisonRequest(
            options=sample_options(),
            time_horizon_months=24,
        )


def test_deterministic_projection_lumpsum():
    req = InvestmentComparisonRequest(
        options=sample_options(),
        investment_amount=Decimal("100000.00"),
        investment_type="lump_sum",
        time_horizon_months=12,
    )
    items = compute_comparison_items(req)

    assert len(items) == 2

    # FD at 7% for 12 months: 100000 * (1 + 0.07/12)^12 = ~107229.01
    fd = items[0]
    assert fd.name == "Bank Fixed Deposit"
    assert fd.projected_future_value is not None
    assert Decimal("107200") < fd.projected_future_value < Decimal("107300")
    assert fd.projected_total_investment == Decimal("100000.00")
    assert fd.projected_total_earnings == fd.projected_future_value - Decimal("100000.00")

    # Index fund at 12% for 12 months: 100000 * (1 + 0.12/12)^12 = 112682.50
    equity = items[1]
    assert equity.projected_future_value == Decimal("112682.50")


def test_deterministic_projection_sip():
    req = InvestmentComparisonRequest(
        options=sample_options(),
        investment_amount=Decimal("10000.00"),
        investment_type="monthly_sip",
        time_horizon_months=12,
    )
    items = compute_comparison_items(req)

    # Equity at 12% SIP for 12 months = 126825.03
    equity = items[1]
    assert equity.projected_total_investment == Decimal("120000.00")
    assert equity.projected_future_value == Decimal("126825.03")
    assert equity.projected_total_earnings == Decimal("6825.03")


def test_prompt_construction_includes_rules_and_disclaimer():
    req = InvestmentComparisonRequest(options=sample_options())
    items = compute_comparison_items(req)
    prompt = build_comparison_prompt(req, items)

    assert "NEVER declare one option as universally" in prompt
    assert "Bank Fixed Deposit" in prompt
    assert "Nifty 50 Index Fund" in prompt


def test_disallowed_certainty_in_explanation_raises_error():
    unsafe_expl = mock_explanation()
    unsafe_expl.summary = "This fund offers guaranteed returns for all investors."

    mock_client = Mock()
    mock_client.models.generate_content.return_value.parsed = unsafe_expl

    req = InvestmentComparisonRequest(options=sample_options())

    with pytest.raises(
        InvestmentComparisonError,
        match="AI comparison contains disallowed certainty or risk-free language",
    ):
        compare_investments(request=req, client=mock_client)


def test_successful_investment_comparison_flow():
    mock_client = Mock()
    mock_client.models.generate_content.return_value.parsed = mock_explanation()

    req = InvestmentComparisonRequest(
        options=sample_options(),
        investment_amount=Decimal("50000.00"),
        investment_type="lump_sum",
        time_horizon_months=24,
    )

    result = compare_investments(request=req, client=mock_client)

    assert isinstance(result, InvestmentComparisonResponse)
    assert len(result.comparison_table) == 2
    assert result.ai_explanation.summary.startswith("Fixed Deposit offers")
    assert result.disclaimer == COMPARISON_DISCLAIMER


def test_investment_comparison_api_endpoint():
    mock_user = User(id=1, email="investor@example.com", hashed_password="pw")

    # Override current user dependency
    app.dependency_overrides[get_current_user] = lambda: mock_user

    client = TestClient(app)

    payload = {
        "options": [
            {
                "name": "Fixed Deposit",
                "category": "fixed_income",
                "expected_annual_return_percent": "7.0",
                "risk_level": "low",
                "liquidity": "moderate",
                "lock_in_period_months": 12,
                "recommended_horizon_months": 12,
                "tax_implications": "Slab rate",
                "capital_protection": "DICGC insurance",
                "advantages": ["Safe"],
                "disadvantages": ["Tax penalty"],
            },
            {
                "name": "Mutual Fund",
                "category": "equity",
                "expected_annual_return_percent": "12.0",
                "risk_level": "high",
                "liquidity": "high",
                "lock_in_period_months": 0,
                "recommended_horizon_months": 36,
                "tax_implications": "LTCG 12.5%",
                "capital_protection": "Market-linked",
                "advantages": ["Growth"],
                "disadvantages": ["Volatility"],
            },
        ],
        "investment_amount": "25000.00",
        "investment_type": "lump_sum",
        "time_horizon_months": 12,
    }

    with patch(
        "app.services.investment_comparison_service.generate_comparison_explanation",
        return_value=mock_explanation(),
    ):
        response = client.post("/investment-comparison/compare", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data["comparison_table"]) == 2
    assert data["ai_explanation"]["summary"].startswith("Fixed Deposit offers")
    assert data["disclaimer"] == COMPARISON_DISCLAIMER
