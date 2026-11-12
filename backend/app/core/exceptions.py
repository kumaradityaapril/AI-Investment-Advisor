from datetime import datetime, timezone
import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception with consistent status and error codes."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Any = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class ExternalAIError(AppException):
    """Raised when external AI providers (e.g. Gemini) fail or time out."""

    def __init__(self, message: str = "External AI service is temporarily unavailable. Please retry shortly."):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="AI_PROVIDER_UNAVAILABLE",
        )


class ResourceNotFoundError(AppException):
    """Raised when a requested resource does not exist or user lacks ownership."""

    def __init__(self, message: str = "Requested resource not found."):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
        )


class PermissionDeniedError(AppException):
    """Raised when an operation violates authorization boundaries."""

    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_DENIED",
        )


class InvalidInputError(AppException):
    """Raised when request payload or parameters fail business validation."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_INPUT",
            details=details,
        )


def _format_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    payload = {
        "error_code": error_code,
        "detail": message,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        payload["details"] = details

    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized, secure exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def handle_app_exception(_request: Request, exc: AppException) -> JSONResponse:
        logger.warning("AppException caught: [%s] %s", exc.error_code, exc.message)
        return _format_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")}
            for err in exc.errors()
        ]
        return _format_error_response(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY),
            error_code="VALIDATION_ERROR",
            message="Request input validation failed.",
            details=errors,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
        # Standardize HTTPException detail
        return _format_error_response(
            status_code=exc.status_code,
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_db_error(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error occurred: %s", exc)
        # CRITICAL: Never leak DB credentials, host, or query SQL in response
        return _format_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
            message="Database service is temporarily unavailable. Please try again shortly.",
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", exc)
        # CRITICAL: Never leak stack trace to client
        return _format_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred. Please contact support.",
        )
