import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class QueryLog(Base):
    """NOT row-level-secured on matter_id (a query spans many matters) - instead scoped
    to user_id, and read only through the /audit route which an admin role can see in
    full. Every query, from every surface, lands here - this is the audit trail."""

    __tablename__ = "query_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="web")  # web | outlook | word
    # Correlates this row to every AgentCallLog row made during the same pipeline run -
    # see services/call_log.py.
    pipeline_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # True if any agent call in this run was served from the raw-response cache rather
    # than a live Gemini call (see agents_sdk/client.py) - e.g. because of a rate limit.
    # The reasoning shown is still a genuine past response, never fabricated.
    replayed_from_cache: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    # The live query's fingerprint is intentionally NOT persisted as an IssueFingerprint
    # row (that table is RLS-scoped by matter_id, and a live query belongs to no matter -
    # forcing a matter_id would either break isolation or fail row-security on insert).
    # Its content is snapshotted here instead, scoped like the rest of this audit row.
    query_fingerprint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    matter_access_scope: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    results_returned: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sources_cited: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    no_confident_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    degraded_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    blocked_by_guardrail: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Full assembled pipeline output, so GET /query/{id} can reconstruct the exact result
    # a user saw (e.g. after a page refresh) without re-running the pipeline.
    full_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
