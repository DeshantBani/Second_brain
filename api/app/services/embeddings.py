"""Gemini embeddings, with graceful degradation baked in: if GEMINI_API_KEY is missing,
invalid, or rate-limited, callers get None back instead of a crash, and the
orchestrator falls back to SQL-only filtering (degraded_mode=True) rather than taking
the app down."""
import logging
import time
from functools import lru_cache

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from app.config import get_settings

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


def embed_text(text: str) -> list[float] | None:
    settings = get_settings()
    client = _get_client()
    if client is None:
        return None

    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimensions),
            )
            return list(response.embeddings[0].values)
        except (ClientError, ServerError) as exc:
            status_code = getattr(exc, "code", None)
            is_last_attempt = attempt == _MAX_ATTEMPTS - 1
            if status_code in _RETRYABLE_STATUS_CODES and not is_last_attempt:
                delay = _RETRY_BASE_DELAY_SECONDS * (2**attempt)
                logger.warning("embedding call error (attempt %d/%d), retrying in %.0fs: %s", attempt + 1, _MAX_ATTEMPTS, delay, exc)
                time.sleep(delay)
                continue
            logger.warning("embedding call failed, degrading gracefully: %s", exc)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("embedding call failed unexpectedly, degrading gracefully: %s", exc)
            return None
    return None
