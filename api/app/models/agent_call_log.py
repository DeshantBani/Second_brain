import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AgentCallLog(Base):
    """Raw log of every single Gemini call (structured-output generations AND
    embeddings) made anywhere in the system - not row-level-secured (infra/audit data,
    admin-visible only via /admin/agent-calls, same category as QueryLog).

    Two jobs:
    1. A complete, inspectable record of exactly what was sent to and received from
       the model for every step of every pipeline run (correlated via
       `pipeline_run_id`, which also lives on QueryLog).
    2. The demo-resilience cache: `cache_key` is a hash of (agent_name, model,
       system_instruction, user_content). When a live call fails, client.py looks up
       the most recent successful row with the same cache_key and replays its
       `raw_response_text` instead of degrading - see agents_sdk/client.py and
       services/embeddings.py. Every successful live call both logs itself AND
       becomes a candidate fallback for any future identical call.
    """

    __tablename__ = "agent_call_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # fingerprint | retrieval | comparison | reusability | reliability | embedding
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    system_instruction: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_response_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    replayed_from_cache: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
