"""Thin seam over the Gemini API so every agent call degrades gracefully instead of
crashing the request when GEMINI_API_KEY is missing/invalid/rate-limited. Nothing else
in the codebase should call the google-genai SDK directly - go through
generate_structured().

No agent-framework "tool calling" loop is used here (see the module docstrings on the
individual agent files for why): every agent call is a single generate_content request
with a Pydantic response_schema for structured output, using data the orchestrator has
already fetched in code. That keeps the pipeline's step order fully code-driven rather
than agent-decided, matches the free tier's tight rate limits (fewer round trips per
query), and sidesteps needing to combine function-calling with schema-constrained
output at all.
"""
import asyncio
import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import TypeVar

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger("second_brain.agents")

T = TypeVar("T", bound=BaseModel)


class AgentError(Exception):
    """Raised whenever an agent call could not complete - missing/invalid API key,
    rate limiting, or any other non-recoverable error. The orchestrator catches this
    and falls back to degraded_mode rather than surfacing a 500."""


class GuardrailTripwireTriggered(Exception):
    """Raised when the citation-verification guardrail finds a claim it cannot ground
    in the source data. Analogous to what an Agents-SDK output guardrail would raise -
    see agents_sdk/citation_guardrail.py. Carries the list of failure reasons."""

    def __init__(self, failures: list[str]):
        self.failures = failures
        super().__init__(f"citation verification failed: {failures}")


class GuardrailFunctionOutput(BaseModel):
    """Minimal stand-in for the OpenAI Agents SDK's GuardrailFunctionOutput - just
    enough shape (output_info + tripwire_triggered) for citation_guardrail.py's
    check to report failures without depending on that SDK."""

    output_info: dict
    tripwire_triggered: bool


@lru_cache
def _get_client() -> genai.Client | None:
    settings = get_settings()
    if not settings.llm_configured:
        return None
    return genai.Client(api_key=settings.gemini_api_key)


@contextmanager
def trace(name: str):
    """Minimal stand-in for the OpenAI Agents SDK's trace() context manager - just
    scopes a log line around one full pipeline run so it's still auditable in the
    server log as a single unit, without depending on that SDK."""
    logger.info("[trace] %s: start", name)
    try:
        yield
    finally:
        logger.info("[trace] %s: end", name)


_RETRYABLE_STATUS_CODES = {429, 503}
_MAX_ATTEMPTS = 3
_RETRY_BASE_DELAY_SECONDS = 2.0


async def generate_structured(model: str, system_instruction: str, user_content: str, response_model: type[T]) -> T:
    """Run one structured-output generation call against Gemini, returning an
    instance of `response_model`. Raises AgentError on any failure (no key, rate
    limit, network, malformed output) so callers never see a raw SDK exception.

    Retries a couple of times, with backoff, on 429 (rate limit) and 503 (transient
    overload - Google's own error message calls these "usually temporary") - both are
    common on a free-tier key under any real load and shouldn't immediately tip a
    whole query into degraded mode."""
    client = _get_client()
    if client is None:
        raise AgentError("GEMINI_API_KEY is not configured")

    response = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_model,
                    temperature=0.2,
                ),
            )
            break
        except (ClientError, ServerError) as exc:
            status_code = getattr(exc, "code", None)
            is_last_attempt = attempt == _MAX_ATTEMPTS - 1
            if status_code in _RETRYABLE_STATUS_CODES and not is_last_attempt:
                delay = _RETRY_BASE_DELAY_SECONDS * (2**attempt)
                logger.warning("Gemini API error (attempt %d/%d), retrying in %.0fs: %s", attempt + 1, _MAX_ATTEMPTS, delay, exc)
                await asyncio.sleep(delay)
                continue
            logger.warning("Gemini API error: %s", exc)
            raise AgentError(f"Gemini API error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - any other failure must also degrade, not crash
            logger.exception("agent generation failed unexpectedly")
            raise AgentError(str(exc)) from exc

    if response.parsed is not None:
        return response.parsed
    # response.parsed can come back None if the model's output didn't strictly
    # validate against the schema on the SDK's own parse attempt - retry validation
    # ourselves against the raw text before giving up, since Pydantic's own validator
    # is sometimes more forgiving (e.g. of extra whitespace) than the SDK's parser.
    try:
        return response_model.model_validate_json(response.text)
    except Exception as exc:
        raise AgentError(f"Gemini response did not match the expected schema: {exc}") from exc
