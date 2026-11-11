
from decimal import Decimal, ROUND_HALF_UP
from typing import TypeAlias


Number: TypeAlias = Decimal | int | float | str

ZERO = Decimal("0")
ONE = Decimal("1")
TWELVE = Decimal("12")
HUNDRED = Decimal("100")
CENT = Decimal("0.01")


class FinancialCalculationError(ValueError):
    """Raised when financial calculation inputs are invalid."""


def _to_decimal(value: Number, field_name: str) -> Decimal:
    """Safely convert a numeric input into Decimal."""

    if isinstance(value, bool):
        raise FinancialCalculationError(
            f"{field_name} must be a valid number."
        )

    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise FinancialCalculationError(
            f"{field_name} must be a valid number."
        ) from exc

    if not result.is_finite():
        raise FinancialCalculationError(
            f"{field_name} must be finite."
        )

    return result


def _non_negative(value: Number, field_name: str) -> Decimal:
    result = _to_decimal(value, field_name)

    if result < ZERO:
        raise FinancialCalculationError(
            f"{field_name} cannot be negative."
        )

    return result


def _positive_months(months: int) -> int:
    if isinstance(months, bool) or not isinstance(months, int):
        raise FinancialCalculationError(
            "Months must be a positive integer."
        )

    if months <= 0:
        raise FinancialCalculationError(
            "Months must be greater than zero."
        )

    return months


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _percentage(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


# --------------------------------------------------
# 1. Cash flow calculations
# --------------------------------------------------

def calculate_monthly_surplus(
    monthly_income: Number,
    monthly_expenses: Number,
) -> Decimal:
    """
    Calculate monthly cash flow.

    A negative result represents a monthly deficit.
    """

    income = _non_negative(monthly_income, "Monthly income")
    expenses = _non_negative(monthly_expenses, "Monthly expenses")

    return _money(income - expenses)


def calculate_annual_income(monthly_income: Number) -> Decimal:
    income = _non_negative(monthly_income, "Monthly income")
    return _money(income * TWELVE)


def calculate_annual_expenses(monthly_expenses: Number) -> Decimal:
    expenses = _non_negative(monthly_expenses, "Monthly expenses")
    return _money(expenses * TWELVE)


# --------------------------------------------------
# 2. Financial ratios
# --------------------------------------------------

def calculate_savings_rate(
    monthly_income: Number,
    monthly_expenses: Number,
) -> Decimal | None:
    """
    Savings rate = (Monthly surplus / Monthly income) * 100.

    Returns None when income is zero.
    """

    income = _non_negative(monthly_income, "Monthly income")
    expenses = _non_negative(monthly_expenses, "Monthly expenses")

    if income == ZERO:
        return None

    surplus = income - expenses

    return _percentage((surplus / income) * HUNDRED)


def calculate_expense_ratio(
    monthly_income: Number,
    monthly_expenses: Number,
) -> Decimal | None:
    """
    Expense ratio = (Monthly expenses / Monthly income) * 100.
    """

    income = _non_negative(monthly_income, "Monthly income")
    expenses = _non_negative(monthly_expenses, "Monthly expenses")

    if income == ZERO:
        return None

    return _percentage((expenses / income) * HUNDRED)


# --------------------------------------------------
# 3. Basic goal calculations
# --------------------------------------------------

def calculate_required_monthly_contribution(
    target_amount: Number,
    time_horizon_months: int,
) -> Decimal:
    """
    Calculate the monthly contribution needed to reach
    a target amount without assuming investment returns.
    """

    target = _non_negative(target_amount, "Target amount")
    months = _positive_months(time_horizon_months)

    return _money(target / Decimal(months))


def calculate_goal_shortfall(
    target_amount: Number,
    current_amount: Number,
) -> Decimal:
    """
    Calculate the remaining amount required for a goal.

    Returns zero when the goal has already been reached.
    """

    target = _non_negative(target_amount, "Target amount")
    current = _non_negative(current_amount, "Current amount")

    return _money(max(ZERO, target - current))


# --------------------------------------------------
# 4. Investment projection helpers
# --------------------------------------------------

def _monthly_rate(annual_return_percent: Number) -> Decimal:
    annual_rate = _non_negative(
        annual_return_percent,
        "Annual return percentage",
    )

    return annual_rate / HUNDRED / TWELVE


def calculate_future_value_lumpsum(
    principal: Number,
    annual_return_percent: Number,
    time_horizon_months: int,
) -> Decimal:
    """
    Future value of a lump-sum investment.

    Formula:
        FV = P * (1 + r)^n

    r = nominal annual return / 12
    n = number of months
    """

    amount = _non_negative(principal, "Principal")
    months = _positive_months(time_horizon_months)
    rate = _monthly_rate(annual_return_percent)

    future_value = amount * (ONE + rate) ** months

    return _money(future_value)


def calculate_future_value_sip(
    monthly_contribution: Number,
    annual_return_percent: Number,
    time_horizon_months: int,
) -> Decimal:
    """
    Future value of monthly end-of-month SIP contributions.

    Formula:
        FV = PMT * (((1 + r)^n - 1) / r)

    When r = 0:
        FV = PMT * n
    """

    payment = _non_negative(
        monthly_contribution,
        "Monthly contribution",
    )
    months = _positive_months(time_horizon_months)
    rate = _monthly_rate(annual_return_percent)

    if rate == ZERO:
        return _money(payment * Decimal(months))

    growth_factor = (ONE + rate) ** months

    future_value = payment * (
        (growth_factor - ONE) / rate
    )

    return _money(future_value)


def calculate_required_monthly_sip(
    target_amount: Number,
    current_amount: Number,
    annual_return_percent: Number,
    time_horizon_months: int,
) -> Decimal:
    """
    Calculate the monthly SIP required to reach a target.

    The current amount is treated as an initial
    lump-sum investment growing for the full period.

    Monthly SIP contributions are assumed to happen
    at the end of each month.
    """

    target = _non_negative(target_amount, "Target amount")
    current = _non_negative(current_amount, "Current amount")
    months = _positive_months(time_horizon_months)
    rate = _monthly_rate(annual_return_percent)

    growth_factor = (ONE + rate) ** months

    future_current_value = current * growth_factor

    remaining_target = target - future_current_value

    if remaining_target <= ZERO:
        return ZERO

    if rate == ZERO:
        return _money(
            remaining_target / Decimal(months)
        )

    sip = remaining_target * rate / (growth_factor - ONE)

    return _money(sip)
