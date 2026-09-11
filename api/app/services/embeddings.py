"""Gemini embeddings, with graceful degradation baked in: if GEMINI_API_KEY is missing,
invalid, or rate-limited, callers get None back instead of a crash, and the
orchestrator falls back to SQL-only filtering (degraded_mode=True) rather than taking
the app down.

Same demo-resilience mechanism as agents_sdk/client.py: every successful embedding is
logged (see services/call_log.py) keyed by a hash of (model, text); if a live call
fails, a prior real embedding for the exact same text is replayed instead of giving up
outright - a query that has embedded successfully once keeps ranking correctly even if
Gemini is unreachable later.
"""
import json
import logging
import time
from functools import lru_cache

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from app.config import get_settings
from app.services.call_log import compute_cache_key, find_cached_response, now_ms, record_call

logger = logging.getLogger("second_brain.embeddings")

_RETRYABLE_STATUS_CODES = {429, 503}
_MAX_ATTEMPTS = 3
_RETRY_BASE_DELAY_SECONDS = 2.0


@lru_cache
def _get_client() -> genai.Client | None:
    settings = get_settings()
    if not settings.llm_configured:
        return None
    return genai.Client(api_key=settings.gemini_api_key)


def _replay_or_none(cache_key: str, model: str, text: str, error_message: str) -> list[float] | None:
    cached_raw = find_cached_response(cache_key)
    if cached_raw is not None:
        try:
            vector = json.loads(cached_raw)
            if isinstance(vector, list):
                logger.warning("live embedding call failed (%s) - replaying a prior real embedding instead", error_message)
                record_call(
                    agent_name="embedding", model=model, cache_key=cache_key, system_instruction="",
                    user_content=text, raw_response_text=cached_raw, success=True, replayed_from_cache=True,
                    error_message=error_message, duration_ms=0,
                )
                return vector
        except (json.JSONDecodeError, TypeError):
            pass

    record_call(
        agent_name="embedding", model=model, cache_key=cache_key, system_instruction="", user_content=text,
        raw_response_text=None, success=False, replayed_from_cache=False, error_message=error_message, duration_ms=0,
    )
    return None


def embed_text(text: str) -> list[float] | None:
    settings = get_settings()
    client = _get_client()
    cache_key = compute_cache_key("embedding", settings.embedding_model, "", text)

    if client is None:
        return _replay_or_none(cache_key, settings.embedding_model, text, "GEMINI_API_KEY is not configured")

    start = now_ms()
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimensions),
            )
            vector = list(response.embeddings[0].values)
            record_call(
                agent_name="embedding", model=settings.embedding_model, cache_key=cache_key, system_instruction="",
                user_content=text, raw_response_text=json.dumps(vector), success=True, replayed_from_cache=False,
                error_message=None, duration_ms=now_ms() - start,
            )
            return vector
        except (ClientError, ServerError) as exc:
            status_code = getattr(exc, "code", None)
            is_last_attempt = attempt == _MAX_ATTEMPTS - 1
            if status_code in _RETRYABLE_STATUS_CODES and not is_last_attempt:
                delay = _RETRY_BASE_DELAY_SECONDS * (2**attempt)
                logger.warning("embedding call error (attempt %d/%d), retrying in %.0fs: %s", attempt + 1, _MAX_ATTEMPTS, delay, exc)
                time.sleep(delay)
                continue
            return _replay_or_none(cache_key, settings.embedding_model, text, str(exc))
        except Exception as exc:  # noqa: BLE001
            return _replay_or_none(cache_key, settings.embedding_model, text, str(exc))
    return None
