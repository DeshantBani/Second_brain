"""Cross-cutting logging + demo-resilience cache for every raw Gemini call (structured
generations in agents_sdk/client.py, and embeddings in services/embeddings.py).

Two things live here:
1. `pipeline_run(...)` / `current_pipeline_run_id()` - a contextvar-based correlation
   id set once per query pipeline run (see services/orchestrator.py), read by every
   agent call so its AgentCallLog row can be joined back to the QueryLog row that
   triggered it, without threading an extra parameter through every agent function.
2. `compute_cache_key`, `record_call`, `find_cached_response` - the actual log-and-
   replay mechanism. Every successful call is persisted with a hash of exactly what
   was sent to the model; when a live call fails (rate limit, outage), the caller looks
   up the most recent successful row with the same hash and replays its real raw
   response instead of falling back to a degraded, reasoning-free result. This is the
   mechanism that lets a live demo survive hitting the free tier's rate limit on a
   query that has already been run successfully at least once before.
"""
import hashlib
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import OwnerSessionLocal
from app.models.agent_call_log import AgentCallLog

logger = logging.getLogger("second_brain.call_log")

_pipeline_run_id: ContextVar[str | None] = ContextVar("pipeline_run_id", default=None)
_run_stats: ContextVar[dict | None] = ContextVar("run_stats", default=None)


@contextmanager
def pipeline_run(run_id: str):
    """Scope every agent/embedding call made inside this block to `run_id`, and start
    a fresh replay-tracking counter for it. See services/orchestrator.py."""
    run_token = _pipeline_run_id.set(run_id)
    stats_token = _run_stats.set({"total": 0, "replayed": 0})
    try:
        yield
    finally:
        _pipeline_run_id.reset(run_token)
        _run_stats.reset(stats_token)


def current_pipeline_run_id() -> str | None:
    return _pipeline_run_id.get()


def record_call_outcome(replayed: bool) -> None:
    stats = _run_stats.get()
    if stats is not None:
        stats["total"] += 1
        if replayed:
            stats["replayed"] += 1


def current_run_had_any_replay() -> bool:
    stats = _run_stats.get()
    return bool(stats and stats["replayed"] > 0)


def compute_cache_key(agent_name: str, model: str, system_instruction: str, user_content: str) -> str:
    payload = f"{agent_name}\n{model}\n{system_instruction}\n{user_content}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record_call(
    *, agent_name: str, model: str, cache_key: str, system_instruction: str, user_content: str,
    raw_response_text: str | None, success: bool, replayed_from_cache: bool,
    error_message: str | None, duration_ms: int,
) -> None:
    """Synchronous - callers (async) should run this via asyncio.to_thread. Uses its
    own short-lived owner session so logging never competes with, or gets rolled back
    by, the request's own RLS-scoped transaction."""
    db = OwnerSessionLocal()
    try:
        db.add(AgentCallLog(
            pipeline_run_id=current_pipeline_run_id(),
            agent_name=agent_name, model=model, cache_key=cache_key,
            system_instruction=system_instruction, user_content=user_content,
            raw_response_text=raw_response_text, success=success, replayed_from_cache=replayed_from_cache,
            error_message=error_message, duration_ms=duration_ms,
        ))
        db.commit()
    except Exception:  # noqa: BLE001 - logging must never be why a request fails
        logger.exception("failed to record agent call log")
        db.rollback()
    finally:
        db.close()

    record_call_outcome(replayed_from_cache)


def find_cached_response(cache_key: str) -> str | None:
    """Synchronous - wrap in asyncio.to_thread. Returns the most recent successful,
    non-replayed raw response for this exact call signature, or None. Excluding
    replayed rows themselves keeps this pointed at an original, real model response
    rather than chaining replays of replays."""
    db = OwnerSessionLocal()
    try:
        row = db.execute(
            select(AgentCallLog)
            .where(AgentCallLog.cache_key == cache_key, AgentCallLog.success.is_(True),
                   AgentCallLog.replayed_from_cache.is_(False))
            .order_by(AgentCallLog.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return row.raw_response_text if row else None
    finally:
        db.close()


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)
