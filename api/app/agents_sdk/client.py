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

Demo-resilience: every successful call is logged (see services/call_log.py) keyed by a
hash of exactly what was sent. If a live call fails for any reason - no key, rate
limit, transient outage - generate_structured() looks for a prior successful response
to that exact same call and replays it instead of raising, so a query that has been
run successfully once keeps working even if Gemini is unreachable when it matters
(mid-presentation). This is never a fabricated result - it's always a real past
response from this same model/prompt, just replayed rather than freshly generated.
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
from app.services.call_log import compute_cache_key, find_cached_response, now_ms, record_call

logger = logging.getLogger("second_brain.agents")

T = TypeVar("T", bound=BaseModel)


class AgentError(Exception):
    """Raised whenever an agent call could not complete AND no cached fallback
    response was available - missing/invalid API key, rate limiting, or any other
    non-recoverable error. The orchestrator catches this and falls back to
    degraded_mode rather than surfacing a 500."""


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


async def _replay_or_raise(
    *, agent_name: str, model: str, cache_key: str, system_instruction: str, user_content: str,
    response_model: type[T], original_error: Exception,
) -> T:
    """The live call didn't work out - look for a prior real response to this exact
    call before giving up. Always logged either way, so the failure (or the replay)
    is visible in the raw call log."""
    cached_raw = await asyncio.to_thread(find_cached_response, cache_key)
    if cached_raw is not None:
        try:
            parsed = response_model.model_validate_json(cached_raw)
        except Exception:  # noqa: BLE001 - a cached row that no longer validates is just not usable
            parsed = None
        if parsed is not None:
            logger.warning(
                "live Gemini call failed for agent=%s (%s) - replaying a prior real response instead",
                agent_name, original_error,
            )
            await asyncio.to_thread(
                record_call, agent_name=agent_name, model=model, cache_key=cache_key,
                system_instruction=system_instruction, user_content=user_content,
                raw_response_text=cached_raw, success=True, replayed_from_cache=True,
                error_message=str(original_error), duration_ms=0,
            )
            return parsed

    await asyncio.to_thread(
        record_call, agent_name=agent_name, model=model, cache_key=cache_key,
        system_instruction=system_instruction, user_content=user_content,
        raw_response_text=None, success=False, replayed_from_cache=False,
        error_message=str(original_error), duration_ms=0,
    )
    raise original_error if isinstance(original_error, AgentError) else AgentError(str(original_error))


async def generate_structured(
    agent_name: str, model: str, system_instruction: str, user_content: str, response_model: type[T],
) -> T:
    """Run one structured-output generation call against Gemini, returning an
    instance of `response_model`. Raises AgentError only if the live call fails AND no
    cached fallback response exists - see module docstring.

    Retries a couple of times, with backoff, on 429 (rate limit) and 503 (transient
    overload - Google's own error message calls these "usually temporary") - both are
    common on a free-tier key under any real load and shouldn't immediately tip a
    whole query into degraded mode."""
    cache_key = compute_cache_key(agent_name, model, system_instruction, user_content)
    client = _get_client()
    if client is None:
        return await _replay_or_raise(
            agent_name=agent_name, model=model, cache_key=cache_key, system_instruction=system_instruction,
            user_content=user_content, response_model=response_model,
            original_error=AgentError("GEMINI_API_KEY is not configured"),
        )

    start = now_ms()
    response = None
    last_error: Exception = AgentError("no attempt was made")
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
            last_error = exc
            status_code = getattr(exc, "code", None)
            is_last_attempt = attempt == _MAX_ATTEMPTS - 1
            if status_code in _RETRYABLE_STATUS_CODES and not is_last_attempt:
                delay = _RETRY_BASE_DELAY_SECONDS * (2**attempt)
                logger.warning("Gemini API error (attempt %d/%d), retrying in %.0fs: %s", attempt + 1, _MAX_ATTEMPTS, delay, exc)
                await asyncio.sleep(delay)
                continue
            logger.warning("Gemini API error: %s", exc)
            break
        except Exception as exc:  # noqa: BLE001 - any other failure must also degrade, not crash
            logger.exception("agent generation failed unexpectedly")
            last_error = exc
            break

    if response is None:
        error = last_error if isinstance(last_error, AgentError) else AgentError(f"Gemini API error: {last_error}")
        return await _replay_or_raise(
            agent_name=agent_name, model=model, cache_key=cache_key, system_instruction=system_instruction,
            user_content=user_content, response_model=response_model, original_error=error,
        )

    duration_ms = now_ms() - start
    raw_text = response.text
    try:
        parsed = response.parsed if response.parsed is not None else response_model.model_validate_json(raw_text)
    except Exception as exc:
        await asyncio.to_thread(
            record_call, agent_name=agent_name, model=model, cache_key=cache_key,
            system_instruction=system_instruction, user_content=user_content,
            raw_response_text=raw_text, success=False, replayed_from_cache=False,
            error_message=f"schema validation failed: {exc}", duration_ms=duration_ms,
        )
        return await _replay_or_raise(
            agent_name=agent_name, model=model, cache_key=cache_key, system_instruction=system_instruction,
            user_content=user_content, response_model=response_model,
            original_error=AgentError(f"Gemini response did not match the expected schema: {exc}"),
        )

    await asyncio.to_thread(
        record_call, agent_name=agent_name, model=model, cache_key=cache_key,
        system_instruction=system_instruction, user_content=user_content,
        raw_response_text=raw_text, success=True, replayed_from_cache=False,
        error_message=None, duration_ms=duration_ms,
    )
    return parsed
