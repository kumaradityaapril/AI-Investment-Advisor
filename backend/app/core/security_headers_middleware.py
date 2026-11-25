"""
Security Headers Middleware.

Injects enterprise defense-in-depth HTTP security headers into all responses:
- Prevents MIME-sniffing (X-Content-Type-Options: nosniff).
- Prevents Clickjacking (X-Frame-Options: DENY).
- Prevents XSS reflection (X-XSS-Protection: 1; mode=block).
- Enforces strict referrer leakage prevention (Referrer-Policy: strict-origin-when-cross-origin).
- Restricts unnecessary browser feature permissions (Permissions-Policy).
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
