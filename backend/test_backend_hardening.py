from unittest.mock import MagicMock
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions import (
    AppException,
    ExternalAIError,
    InvalidInputError,
    PermissionDeniedError,
    ResourceNotFoundError,
    register_exception_handlers,
)
from app.core.logging_middleware import AuditLoggingMiddleware
from app.main import app as main_app
from app.services.gemini_reliability_service import call_with_retry

main_client = TestClient(main_app)


# -------------------------------------------------------------
# 1. Centralized Exception Handling Tests
# -------------------------------------------------------------

@pytest.fixture
def test_app():
    test_api = FastAPI()
    test_api.add_middleware(AuditLoggingMiddleware)
    register_exception_handlers(test_api)

    router = APIRouter()

    @router.get("/test/app-exception")
    def trigger_app_exc():
        raise AppException("Custom app failure", status_code=418, error_code="TEAPOT_ERROR")

    @router.get("/test/external-ai-error")
    def trigger_ai_exc():
        raise ExternalAIError("Gemini timed out")

    @router.get("/test/not-found")
    def trigger_not_found():
        raise ResourceNotFoundError("Goal 99 not found")

    @router.get("/test/permission-denied")
    def trigger_perm_denied():
        raise PermissionDeniedError("Cannot access this portfolio")

    @router.get("/test/invalid-input")
    def trigger_invalid_input():
        raise InvalidInputError("Negative monthly income is not allowed", details={"field": "income"})

    @router.get("/test/db-error")
    def trigger_db_error():
        # Sensitive DB details that must never be exposed
        raise OperationalError(
            statement="SELECT * FROM users WHERE password='super_secret_password'",
            params={},
            orig=Exception("FATAL: connection to 10.0.0.1:5432 failed password authentication for user 'admin'"),
        )

    @router.get("/test/unhandled-error")
    def trigger_unhandled():
        raise RuntimeError("Unexpected zero division or crash in internal helper")

    test_api.include_router(router)
    return test_api


def test_custom_app_exception_handling(test_app):
    client = TestClient(test_app)
    res = client.get("/test/app-exception")
    assert res.status_code == 418
    data = res.json()
    assert data["error_code"] == "TEAPOT_ERROR"
    assert data["message"] == "Custom app failure"
    assert "timestamp" in data


def test_external_ai_error_handling(test_app):
    client = TestClient(test_app)
    res = client.get("/test/external-ai-error")
    assert res.status_code == 503
    data = res.json()
    assert data["error_code"] == "AI_PROVIDER_UNAVAILABLE"


def test_resource_not_found_handling(test_app):
    client = TestClient(test_app)
    res = client.get("/test/not-found")
    assert res.status_code == 404
    data = res.json()
    assert data["error_code"] == "RESOURCE_NOT_FOUND"


def test_permission_denied_handling(test_app):
    client = TestClient(test_app)
    res = client.get("/test/permission-denied")
    assert res.status_code == 403
    data = res.json()
    assert data["error_code"] == "PERMISSION_DENIED"


def test_invalid_input_handling(test_app):
    client = TestClient(test_app)
    res = client.get("/test/invalid-input")
    assert res.status_code == 400
    data = res.json()
    assert data["error_code"] == "INVALID_INPUT"
    assert data["details"] == {"field": "income"}


def test_database_error_sanitization(test_app):
    client = TestClient(test_app)
    res = client.get("/test/db-error")
    assert res.status_code == 503
    data = res.json()
    assert data["error_code"] == "DATABASE_UNAVAILABLE"
    # Verify no sensitive DB passwords, IPs, or credentials leaked
    response_text = res.text
    assert "super_secret_password" not in response_text
    assert "10.0.0.1" not in response_text
    assert "admin" not in response_text


def test_unhandled_error_hides_stack_trace(test_app):
    client = TestClient(test_app, raise_server_exceptions=False)
    res = client.get("/test/unhandled-error")
    assert res.status_code == 500
    data = res.json()
    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    assert "Traceback" not in res.text
    assert "zero division" not in res.text


# -------------------------------------------------------------
# 2. AI Provider Reliability & Retry Tests
# -------------------------------------------------------------

def test_call_with_retry_succeeds_first_attempt():
    mock_fn = MagicMock(return_value="SUCCESS_RESULT")
    result = call_with_retry(mock_fn, max_retries=3, initial_delay_seconds=0.01)
    assert result == "SUCCESS_RESULT"
    assert mock_fn.call_count == 1


def test_call_with_retry_succeeds_after_transient_failure():
    mock_fn = MagicMock(
        side_effect=[
            RuntimeError("Temporary 503 Service Unavailable"),
            "RECOVERED_SUCCESS",
        ]
    )
    result = call_with_retry(mock_fn, max_retries=3, initial_delay_seconds=0.01)
    assert result == "RECOVERED_SUCCESS"
    assert mock_fn.call_count == 2


def test_call_with_retry_exhausted_raises_external_ai_error():
    mock_fn = MagicMock(side_effect=RuntimeError("Persistent Gemini connection timeout"))
    with pytest.raises(ExternalAIError, match="failed after 3 retry attempts"):
        call_with_retry(mock_fn, max_retries=3, initial_delay_seconds=0.01)
    assert mock_fn.call_count == 3


# -------------------------------------------------------------
# 3. Audit Logging Middleware Tests
# -------------------------------------------------------------

def test_audit_logging_middleware_headers(test_app):
    client = TestClient(test_app)
    res = client.get("/test/app-exception")
    assert "X-Request-ID" in res.headers
    assert "X-Process-Time" in res.headers
    assert res.headers["X-Process-Time"].endswith("ms")


def test_audit_logging_middleware_propagates_incoming_request_id(test_app):
    client = TestClient(test_app)
    custom_id = "custom-client-trace-12345"
    res = client.get("/test/app-exception", headers={"x-request-id": custom_id})
    assert res.headers["X-Request-ID"] == custom_id
