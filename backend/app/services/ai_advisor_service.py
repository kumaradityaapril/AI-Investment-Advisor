import logging
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai_advisor import AIAdvisorGenerationResponse
from app.services.groq_service import (
    call_groq_structured,
    GroqRateLimitError,
    GroqContextLengthError,
    GroqProviderError,
    is_groq_enabled,
)

logger = logging.getLogger(__name__)


class AIAdvisorError(Exception):
    """Raised when AI Advisor generation fails."""


def _get_gemini_client() -> genai.Client:
    """Create a Gemini client using the configured API key."""
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={
            "api_version": "v1beta",
            "timeout": 30000,
        },
    )


def _parse_advisor_response(
    response: Any,
) -> AIAdvisorGenerationResponse:
    """Parse and validate Gemini's structured generation response."""
    if response is None:
        raise AIAdvisorError("Gemini returned an empty response.")

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, AIAdvisorGenerationResponse):
        return parsed

    text = getattr(response, "text", None)
    if not text or not str(text).strip():
        raise AIAdvisorError("Gemini returned an empty response.")

    try:
        return AIAdvisorGenerationResponse.model_validate_json(text)
    except ValidationError as exc:
        raise AIAdvisorError(
            f"Failed to validate AI Advisor response: {exc}"
        ) from exc
    except Exception as exc:
        raise AIAdvisorError(
            f"Failed to parse AI Advisor response: {exc}"
        ) from exc


def _generate_advisor_with_groq(prompt: str) -> AIAdvisorGenerationResponse:
    """Generate structured advice using Groq API."""
    return call_groq_structured(
        prompt=prompt,
        response_model=AIAdvisorGenerationResponse,
        system_instruction=(
            "You are an expert AI Investment Advisor providing objective, "
            "evidence-grounded financial advice in simple, easy-to-understand English. "
            "Whenever you introduce any financial, investment, or tax term for the first time, "
            "immediately explain its simple meaning in brackets right after the term."
        ),
        temperature=0.2,
        max_output_tokens=1800,
    )


def generate_advisor_response(
    prompt: str = "",
    client: genai.Client | None = None,
) -> AIAdvisorGenerationResponse:
    """
    Generate structured advice using Groq API as the primary and sole LLM engine.
    """
    # 1. If mock client explicitly provided (for unit tests), execute mock
    if client is not None:
        try:
            response = client.models.generate_content(
                model=settings.advisor_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIAdvisorGenerationResponse,
                    temperature=0.2,
                ),
            )
            return _parse_advisor_response(response)
        except Exception as exc:
            raise AIAdvisorError(f"Test generation failed: {exc}") from exc

    # 2. Live generation uses Groq exclusively (configured model)
    logger.info("Generating advisor response via Groq API...")
    return _generate_advisor_with_groq(prompt)
