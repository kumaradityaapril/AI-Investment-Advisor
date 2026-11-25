import os
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import settings
from app.core.rate_limit_middleware import RateLimitRule, SlidingWindowRateLimiter
from app.main import app
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.goal import GoalCreate


@pytest.fixture
def client():
    # Use TestClient with engine.connect mocked so no DB socket timeouts occur
    os.environ["TESTING"] = "0"
    mock_conn = MagicMock()
    with patch("app.main.engine.connect", return_value=mock_conn):
        with TestClient(app) as test_client:
            yield test_client
    os.environ["TESTING"] = "1"


def test_api_keys_are_masked_in_settings_repr():
    """Verify that settings repr and str never expose secrets."""
    rep = repr(settings)
    s = str(settings)

    # Must contain safe identifier
    assert "Settings" in rep
    assert "development" in rep or "production" in rep or "test" in rep

    # Must NOT contain actual raw keys
    if settings.groq_api_key:
        assert settings.groq_api_key not in rep
        assert settings.groq_api_key not in s
    if settings.gemini_api_key:
        assert settings.gemini_api_key not in rep
        assert settings.gemini_api_key not in s
    if settings.jwt_secret_key:
        assert settings.jwt_secret_key not in rep
        assert settings.jwt_secret_key not in s


def test_security_headers_present_on_all_responses(client):
    """Verify that institutional security headers are injected on responses."""
    resp = client.get("/health")
    assert resp.status_code == 200

    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("Permissions-Policy", "")


def test_health_endpoint_does_not_leak_keys(client):
    """Verify that health check reports status without leaking any API keys."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "healthy"
    assert data["rate_limiting"] == "active"
    assert data["security_headers"] == "active"
    assert "api_key" not in data
    assert "groq_api_key" not in data
    assert "gemini_api_key" not in data
    assert "jwt_secret_key" not in data


def test_sliding_window_rate_limiter_logic():
    """Verify pure rate limiter logic throttles when limit is reached and resets correctly."""
    limiter = SlidingWindowRateLimiter()
    rule = RateLimitRule(limit=3, window_seconds=10)
    client_id = "test_client_ip_1"

    # First 3 requests must succeed
    for _ in range(3):
        allowed, retry_after = limiter.is_allowed(client_id, rule)
        assert allowed is True
        assert retry_after == 0

    # 4th request must be rejected with retry_after > 0
    allowed, retry_after = limiter.is_allowed(client_id, rule)
    assert allowed is False
    assert retry_after >= 1


def test_input_validation_register_sanitization():
    """Verify RegisterRequest strips/lowercases email and rejects malicious script tags in name."""
    # Valid registration
    valid = RegisterRequest(
        name="  Kumar Aditya  ",
        email="  INVESTOR@Example.COM  ",
        password="ValidPassword123!",
    )
    assert valid.name == "Kumar Aditya"
    assert valid.email == "investor@example.com"

    # Malicious script tag in name must be rejected
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="<script>alert(1)</script>",
            email="safe@example.com",
            password="ValidPassword123!",
        )

    # Null bytes must be rejected
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="Investor\0Hacker",
            email="safe@example.com",
            password="ValidPassword123!",
        )


def test_input_validation_login_email_normalization():
    """Verify LoginRequest normalizes email."""
    req = LoginRequest(
        email="  USER@Finance.in ",
        password="secretpassword",
    )
    assert req.email == "user@finance.in"


def test_input_validation_goal_target_amount_bounds():
    """Verify GoalCreate rejects negative amounts and excessive numbers."""
    # Negative target amount rejected
    with pytest.raises(ValidationError):
        GoalCreate(
            title="Retirement",
            goal_type="retirement",
            target_amount=Decimal("-50000"),
            time_horizon_months=120,
        )

    # Excessive target amount beyond ceiling rejected
    with pytest.raises(ValidationError):
        GoalCreate(
            title="Impossible Corpus",
            goal_type="other",
            target_amount=Decimal("999999999999999999"),
            time_horizon_months=120,
        )

    # Valid goal succeeds
    goal = GoalCreate(
        title="Retirement Corpus",
        goal_type="retirement",
        target_amount=Decimal("15000000.00"),
        time_horizon_months=180,
    )
    assert goal.target_amount == Decimal("15000000.00")
    assert goal.time_horizon_months == 180
