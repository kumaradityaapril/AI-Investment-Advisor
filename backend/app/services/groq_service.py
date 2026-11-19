import json
import logging
import re
import time
from typing import Any, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MAX_OUTPUT_TOKENS = 1800
MAX_ALLOWED_OUTPUT_TOKENS = 3500
MAX_RATE_LIMIT_WAIT_SECONDS = 16.0


class GroqRateLimitError(Exception):
    """Raised when Groq rate or token limits are exceeded."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class GroqContextLengthError(Exception):
    """Raised when the request exceeds the model context window."""
    pass


class GroqProviderError(Exception):
    """Raised for other Groq API or communication failures."""
    pass


def is_groq_enabled() -> bool:
    """Check whether Groq is configured."""
    return bool(settings.groq_api_key.strip())


def _resolve_working_model() -> str:
    """Use only the explicitly configured Groq model."""
    model = (settings.groq_model or "").strip()
    if not model:
        raise GroqProviderError("GROQ_MODEL is not configured.")
    return model


def _clean_json_text(content: str) -> str:
    """Extract a JSON object from the model response."""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        content = content[first_brace : last_brace + 1]
    return content.strip()


def _resolve_schema_node(node: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in node:
        ref_name = node["$ref"].split("/")[-1]
        return defs.get(ref_name, node)
    return node


def _is_array_schema(node: dict[str, Any], defs: dict[str, Any]) -> bool:
    node = _resolve_schema_node(node, defs)
    if node.get("type") == "array":
        return True
    for branch in node.get("anyOf", []):
        if _resolve_schema_node(branch, defs).get("type") == "array":
            return True
    return False


def _unwrap_schema_arrays(obj: Any, schema: dict[str, Any], defs: dict[str, Any]) -> Any:
    """Unwrap Groq's occasional {'items': [...]} wrapper when the schema expects an array."""
    node = _resolve_schema_node(schema, defs)
    if isinstance(obj, dict):
        if _is_array_schema(node, defs):
            for key in ("items", "values", "elements", "results", "data"):
                if isinstance(obj.get(key), list):
                    obj = obj[key]
                    break
            else:
                return obj
        else:
            props = node.get("properties", {})
            return {
                k: _unwrap_schema_arrays(v, props[k], defs) if k in props else v
                for k, v in obj.items()
            }
    if isinstance(obj, list):
        item_schema = node.get("items")
        if not item_schema:
            for branch in node.get("anyOf", []):
                resolved = _resolve_schema_node(branch, defs)
                if resolved.get("type") == "array" and "items" in resolved:
                    item_schema = resolved["items"]
                    break
        if isinstance(item_schema, dict):
            return [_unwrap_schema_arrays(el, item_schema, defs) for el in obj]
    return obj


def _parse_retry_after(headers: httpx.Headers, body_text: str) -> float | None:
    """Extract retry-after delay in seconds from response headers or error body if present."""
    header_val = headers.get("retry-after")
    if header_val:
        try:
            return float(header_val)
        except ValueError:
            pass

    try:
        match = re.search(r"try again in (\d+(?:\.\d+)?)\s*(s|ms)", body_text)
        if match:
            val = float(match.group(1))
            unit = match.group(2)
            return val if unit == "s" else val / 1000.0
    except Exception:
        pass

    return None


def call_groq_structured(
    prompt: str,
    response_model: type[T],
    system_instruction: str = "You are an expert AI financial advisor.",
    temperature: float = 0.2,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    timeout: float = 45.0,
) -> T:
    """
    Call Groq API using the explicitly configured model, compact schema, and typed error handling.
    """
    api_key = settings.groq_api_key.strip()
    if not api_key:
        raise GroqProviderError("GROQ_API_KEY is not configured in backend/.env.")

    model = _resolve_working_model()
    tokens_budget = min(max_output_tokens, MAX_ALLOWED_OUTPUT_TOKENS)

    schema_dict = response_model.model_json_schema()
    required_keys = list(schema_dict.get("properties", {}).keys())

    full_system = (
        f"{system_instruction}\n\n"
        "CRITICAL JSON OUTPUT RULES:\n"
        "1. You MUST generate ONLY a single valid JSON object.\n"
        "2. Do NOT echo or copy the investor profile or financial context from the prompt.\n"
        f"3. The root JSON object MUST start with '{{' and contain these exact top-level keys: {json.dumps(required_keys)}\n"
        "4. Output raw JSON ONLY. No markdown code fences, no extra text.\n"
        f"5. The JSON must adhere to this JSON Schema: {json.dumps(schema_dict, separators=(',', ':'))}\n"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": temperature,
        "max_tokens": tokens_budget,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                GROQ_CHAT_COMPLETIONS_URL,
                headers=headers,
                json=payload,
            )

            # 429: Rate / TPM limit exceeded — wait briefly and retry once if within budget
            if resp.status_code == 429:
                retry_sec = _parse_retry_after(resp.headers, resp.text)
                if retry_sec is not None and 0 < retry_sec <= MAX_RATE_LIMIT_WAIT_SECONDS:
                    wait_sec = min(retry_sec + 0.5, MAX_RATE_LIMIT_WAIT_SECONDS + 0.5)
                    logger.warning(
                        "Groq TPM rate limit hit (429); sleeping %.1fs before automatic retry...",
                        wait_sec,
                    )
                    time.sleep(wait_sec)
                    resp = client.post(
                        GROQ_CHAT_COMPLETIONS_URL,
                        headers=headers,
                        json=payload,
                    )

            if resp.status_code == 429:
                retry_sec = _parse_retry_after(resp.headers, resp.text)
                logger.error("Groq rate limit exceeded (429): %s (retry_after=%s)", resp.text, retry_sec)
                raise GroqRateLimitError(
                    f"Groq rate limit / TPM budget exceeded: {resp.text}",
                    retry_after=retry_sec,
                )

            # 400: Context length exceeded or JSON validation failed
            if resp.status_code == 400:
                if "context_length_exceeded" in resp.text:
                    logger.error("Groq context length exceeded (400): %s", resp.text)
                    raise GroqContextLengthError(
                        "The prompt exceeds the Groq model's context window limit. Please reduce document or prompt size."
                    )
                if "json_validate_failed" in resp.text:
                    logger.warning("Groq response_format gate rejected, retrying without strict gate...")
                    unconstrained_payload = dict(payload)
                    del unconstrained_payload["response_format"]
                    resp = client.post(
                        GROQ_CHAT_COMPLETIONS_URL,
                        headers=headers,
                        json=unconstrained_payload,
                    )
                    if resp.status_code == 429:
                        retry_sec = _parse_retry_after(resp.headers, resp.text)
                        raise GroqRateLimitError(
                            f"Groq rate limit / TPM budget exceeded: {resp.text}",
                            retry_after=retry_sec,
                        )
                    if resp.status_code != 200:
                        raise GroqProviderError(f"Groq rejected unconstrained retry ({resp.status_code}): {resp.text}")

            # 404: Model not found
            if resp.status_code == 404:
                raise GroqProviderError(
                    f"Configured Groq model '{model}' is not available for this API key: {resp.text}"
                )

            # Any other non-200
            if resp.status_code != 200:
                raise GroqProviderError(f"Groq API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("Successfully generated structured response via Groq (%s)", model)

    except (GroqRateLimitError, GroqContextLengthError, GroqProviderError):
        raise
    except httpx.TimeoutException as exc:
        logger.error("Groq request timed out: %s", exc)
        raise GroqProviderError(f"Groq request timed out: {exc}") from exc
    except httpx.RequestError as exc:
        logger.error("Groq communication failure: %s", exc)
        raise GroqProviderError(f"Groq communication failure: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error communicating with Groq: %s", exc)
        raise GroqProviderError(f"Unexpected error communicating with Groq: {exc}") from exc

    cleaned = _clean_json_text(content)

    try:
        parsed_raw = json.loads(cleaned)
        normalized = _unwrap_schema_arrays(parsed_raw, schema_dict, schema_dict.get("$defs", {}))
        return response_model.model_validate(normalized)
    except json.JSONDecodeError as exc:
        logger.error("Groq output was not valid JSON: %s\nCleaned content was: %s", exc, cleaned)
        raise GroqProviderError(f"Groq output was not valid JSON: {exc}") from exc
    except ValidationError as exc:
        logger.error("Groq JSON output failed schema validation: %s\nCleaned content was: %s", exc, cleaned)
        raise GroqProviderError(f"Groq output failed schema validation: {exc}") from exc
