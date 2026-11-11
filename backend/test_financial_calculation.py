
from decimal import Decimal

import pytest

from app.services.financial_calculation_service import (
    FinancialCalculationError,
    calculate_monthly_surplus,
    calculate_annual_income,
    calculate_annual_expenses,
    calculate_savings_rate,
    calculate_expense_ratio,
    calculate_required_monthly_contribution,
    calculate_goal_shortfall,
    calculate_future_value_lumpsum,
    calculate_future_value_sip,
    calculate_required_monthly_sip,
)


def test_cash_flow_calculations():
    assert calculate_monthly_surplus(
        100000, 60000
    ) == Decimal("40000.00")

    assert calculate_monthly_surplus(
        50000, 60000
    ) == Decimal("-10000.00")

    assert calculate_annual_income(
        100000
    ) == Decimal("1200000.00")

    assert calculate_annual_expenses(
        60000
    ) == Decimal("720000.00")


def test_financial_ratios():
    assert calculate_savings_rate(
        100000, 60000
    ) == Decimal("40.00")

    assert calculate_expense_ratio(
        100000, 60000
    ) == Decimal("60.00")

    assert calculate_savings_rate(
        0, 0
    ) is None

    assert calculate_expense_ratio(
        0, 0
    ) is None


def test_goal_calculations():
    assert calculate_required_monthly_contribution(
        1200000, 120
    ) == Decimal("10000.00")

    assert calculate_goal_shortfall(
        1000000, 400000
    ) == Decimal("600000.00")

    assert calculate_goal_shortfall(
        1000000, 1200000
    ) == Decimal("0.00")


def test_lumpsum_future_value_without_returns():
    assert calculate_future_value_lumpsum(
        100000, 0, 12
    ) == Decimal("100000.00")


def test_sip_future_value_without_returns():
    assert calculate_future_value_sip(
        10000, 0, 12
    ) == Decimal("120000.00")


def test_lumpsum_future_value_with_returns():
    result = calculate_future_value_lumpsum(
        100000, 12, 12
    )

    assert result > Decimal("100000.00")


def test_sip_future_value_with_returns():
    result = calculate_future_value_sip(
        10000, 12, 12
    )

    assert result > Decimal("120000.00")


def test_required_sip_without_returns():
    assert calculate_required_monthly_sip(
        120000, 0, 0, 12
    ) == Decimal("10000.00")


def test_required_sip_with_existing_investment():
    result = calculate_required_monthly_sip(
        1200000, 200000, 0, 100
    )

    assert result == Decimal("10000.00")


def test_required_sip_when_goal_already_reached():
    assert calculate_required_monthly_sip(
        100000, 150000, 12, 12
    ) == Decimal("0.00")


def test_negative_values_are_rejected():
    with pytest.raises(FinancialCalculationError):
        calculate_monthly_surplus(-1000, 500)

    with pytest.raises(FinancialCalculationError):
        calculate_future_value_sip(1000, -5, 12)

    with pytest.raises(FinancialCalculationError):
        calculate_goal_shortfall(100000, -500)


def test_invalid_time_horizon_is_rejected():
    with pytest.raises(FinancialCalculationError):
        calculate_required_monthly_contribution(
            100000, 0
        )

    with pytest.raises(FinancialCalculationError):
        calculate_future_value_sip(
            1000, 12, -10
        )


def test_non_finite_values_are_rejected():
    with pytest.raises(FinancialCalculationError):
        calculate_monthly_surplus("NaN", 1000)

    with pytest.raises(FinancialCalculationError):
        calculate_future_value_sip(
            "Infinity", 12, 12
        )


def test_invalid_boolean_inputs_are_rejected():
    with pytest.raises(FinancialCalculationError):
        calculate_monthly_surplus(True, 1000)
