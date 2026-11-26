from contextlib import asynccontextmanager
import logging
import os
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.goals import router as goals_router
from app.api.profile import router as profile_router
from app.api.risk_assessments import router as risk_assessments_router
from app.core.config import settings
from app.core.database import engine, get_db
from app.api.documents import router as documents_router
from app.api.financial_analysis import router as financial_analysis_router
from app.api.investment_comparison import router as investment_comparison_router
from app.api.advisor import router as advisor_router
from app.api.research import router as research_router
from app.api.scenarios import router as scenarios_router
from app.core.exceptions import register_exception_handlers
from app.core.logging_middleware import AuditLoggingMiddleware
from app.core.rate_limit_middleware import RateLimitMiddleware
from app.core.security_headers_middleware import SecurityHeadersMiddleware

from app.services.advisor_orchestration_service import (
    AdvisorOrchestrationError,
)
from app.services.groq_service import (
    GroqContextLengthError,
    GroqProviderError,
    GroqRateLimitError,
)
from app.services.investment_comparison_service import (
    InvestmentComparisonError,
)

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-ensure database schema columns exist (e.g. users.name)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255);")
            )
            conn.commit()
            logger.info("Database schema verified: users.name column ensured.")
    except Exception as exc:
        logger.warning(
            "Database connection check at startup deferred: %s", exc
        )
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="GenAI-powered AI Investment Advisor API",
    lifespan=lifespan,
)


def find_groq_error(exc: BaseException) -> Exception | None:
    """Find a Groq exception inside a wrapped exception chain."""
    current: BaseException | None = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(
            current,
            (
                GroqRateLimitError,
                GroqContextLengthError,
                GroqProviderError,
            ),
        ):
            return current
        current = current.__cause__ or current.__context__
    return None


def build_groq_error_response(exc: BaseException) -> JSONResponse:
    """Convert Groq failures into appropriate HTTP responses."""
    groq_error = find_groq_error(exc) or exc

    if isinstance(groq_error, GroqRateLimitError):
        headers = {}
        if groq_error.retry_after is not None:
            headers["Retry-After"] = str(max(1, int(groq_error.retry_after)))
        return JSONResponse(
            status_code=429,
            content={
                "error_code": "AI_PROVIDER_RATE_LIMIT",
                "message": "AI provider rate limit reached. Please retry shortly.",
                "detail": "AI provider rate limit reached. Please retry shortly.",
            },
            headers=headers,
        )

    if isinstance(groq_error, GroqContextLengthError):
        return JSONResponse(
            status_code=502,
            content={
                "error_code": "AI_CONTEXT_LIMIT_EXCEEDED",
                "message": "The AI prompt exceeds the model's context limit.",
                "detail": "The AI prompt exceeds the model's context limit.",
            },
        )

    if isinstance(groq_error, GroqProviderError):
        return JSONResponse(
            status_code=502,
            content={
                "error_code": "AI_PROVIDER_UNAVAILABLE",
                "message": "AI service is temporarily unavailable. Please retry shortly.",
                "detail": "AI service is temporarily unavailable. Please retry shortly.",
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "error_code": "AI_GENERATION_FAILED",
            "message": "Failed to generate AI financial analysis.",
            "detail": "Failed to generate AI financial analysis.",
        },
    )


@app.exception_handler(AdvisorOrchestrationError)
async def handle_advisor_orchestration_error(
    _request: Request, exc: AdvisorOrchestrationError
) -> JSONResponse:
    return build_groq_error_response(exc)


@app.exception_handler(InvestmentComparisonError)
async def handle_investment_comparison_error(
    _request: Request, exc: InvestmentComparisonError
) -> JSONResponse:
    return build_groq_error_response(exc)


@app.exception_handler(GroqRateLimitError)
async def handle_groq_rate_limit(
    _request: Request, exc: GroqRateLimitError
) -> JSONResponse:
    return build_groq_error_response(exc)


@app.exception_handler(GroqContextLengthError)
async def handle_groq_context_length(
    _request: Request, exc: GroqContextLengthError
) -> JSONResponse:
    return build_groq_error_response(exc)


@app.exception_handler(GroqProviderError)
async def handle_groq_provider_error(
    _request: Request, exc: GroqProviderError
) -> JSONResponse:
    return build_groq_error_response(exc)


@app.exception_handler(HTTPException)
async def handle_http_exception(
    _request: Request, exc: HTTPException
) -> JSONResponse:
    groq_error = find_groq_error(exc)
    if groq_error is not None:
        return build_groq_error_response(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "detail": str(exc.detail),
        },
    )


app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ai-investment-advisor-inky.vercel.app",
    "https://ai-investment-advisor-git-main-kumaradityaaprils-projects.vercel.app",
    "https://ai-investment-advisor-nqo1mcvs7-kumaradityaaprils-projects.vercel.app",
]
extra_origins = os.getenv("FRONTEND_URL", "")
if extra_origins:
    cors_origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(goals_router)
app.include_router(risk_assessments_router)
app.include_router(documents_router)
app.include_router(financial_analysis_router)
app.include_router(investment_comparison_router)
app.include_router(advisor_router)
app.include_router(research_router)
app.include_router(scenarios_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-investment-advisor-api",
        "version": "1.0.1-cors-all",
        "rate_limiting": "active",
        "security_headers": "active",
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    value = result.scalar()
    return {
        "status": "healthy",
        "database": "connected",
        "result": value,
    }


@app.get("/health/vector")
def vector_health_check(db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            SELECT
                '[1,2,3]'::vector <-> '[1,2,4]'::vector
                AS distance
        """)
    )
    distance = result.scalar()
    return {
        "status": "healthy",
        "extension": "pgvector",
        "vector_operation": "successful",
        "distance": distance,
    }
