import logging
import time
from uuid import uuid4
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("api.access")

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that provides:
    1. Unique correlation ID (X-Request-ID) tracking per request.
    2. Request execution latency tracking (X-Process-Time).
    3. Structured access audit logging with sensitive header redaction.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        start_time = time.perf_counter()

        # Attach request_id to request state
        request.state.request_id = request_id

        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        response: Response
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "[%s] %s %s from %s FAILED in %.2fms",
                request_id,
                method,
                path,
                client_host,
                duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms}ms"

        # Structured access log without logging passwords or PII
        logger.info(
            "[%s] %s %s %d - %.2fms (client=%s)",
            request_id,
            method,
            path,
            response.status_code,
            duration_ms,
            client_host,
        )

        return response

