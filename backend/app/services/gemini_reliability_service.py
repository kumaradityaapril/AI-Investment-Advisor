import asyncio
import logging
import time
from typing import Any, Callable

from google.genai.errors import APIError

from app.core.exceptions import ExternalAIError

logger = logging.getLogger(__name__)

TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


def call_with_retry(
    fn: Callable[[], Any],
    max_retries: int = 3,
    initial_delay_seconds: float = 0.5,
    backoff_factor: float = 2.0,
    operation_name: str = "Gemini API call",
) -> Any:
    """
    Execute a synchronous call to Gemini with exponential backoff for transient failures.
    Fast-fails on permanent client errors (400, 401, 403).
    """
    delay = initial_delay_seconds
    last_exception: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except APIError as exc:
            last_exception = exc
            status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)

            # Permanent failure: do not waste retry attempts
            if status_code is not None and status_code not in TRANSIENT_STATUS_CODES:
                logger.error(
                    "Permanent %s error (%s): %s. Fast-failing without retry.",
                    operation_name,
                    status_code,
                    exc,
                )
                raise ExternalAIError(
                    f"{operation_name} failed permanently with code {status_code}: {exc}"
                ) from exc

            # Transient failure
            if attempt < max_retries:
                logger.warning(
                    "%s transient failure (%s) on attempt %d/%d. Retrying in %.2fs: %s",
                    operation_name,
                    status_code or "transient",
                    attempt,
                    max_retries,
                    delay,
                    exc,
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    "%s failed after %d attempts. Giving up: %s",
                    operation_name,
                    max_retries,
                    exc,
                )

        except Exception as exc:
            last_exception = exc
            if attempt < max_retries:
                logger.warning(
                    "%s unexpected error on attempt %d/%d. Retrying in %.2fs: %s",
                    operation_name,
                    attempt,
                    max_retries,
                    delay,
                    exc,
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    "%s exhausted all %d attempts: %s",
                    operation_name,
                    max_retries,
                    exc,
                )

    raise ExternalAIError(
        f"{operation_name} failed after {max_retries} retry attempts: {last_exception}"
    ) from last_exception

