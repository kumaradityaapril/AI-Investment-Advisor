import logging
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai_advisor import AIAdvisorGenerationResponse

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


def generate_advisor_response(
    prompt: str = "",
    client: genai.Client | None = None,
) -> AIAdvisorGenerationResponse:
    """
    Generate structured advice from Gemini using the generation schema.
    """
    if client is None:
        try:
            client = _get_gemini_client()
        except Exception as exc:
            raise AIAdvisorError(
                f"Failed to initialize Gemini client: {exc}"
            ) from exc

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
    except Exception as exc:
        raise AIAdvisorError(
            f"Gemini advisor generation failed: {exc}"
        ) from exc

    return _parse_advisor_response(response)
