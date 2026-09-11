import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.db import Base

settings = get_settings()


class IssueFingerprint(Base):
    """RLS-protected via matter_id. One persisted row per matter, generated at
    ingestion time and used as a retrieval candidate. `is_ephemeral` is reserved for a
    future ephemeral-fingerprint use case; live incoming queries do NOT create a row
    here (they have no matter_id to scope to) - their fingerprint is snapshotted
    directly onto QueryLog.query_fingerprint instead. See services/orchestrator.py."""

    __tablename__ = "issue_fingerprints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), nullable=True, index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    is_ephemeral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False)
    practice_area: Mapped[str] = mapped_column(String(100), nullable=False)
    procedural_posture: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    factual_pattern: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    contract_clauses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    clause_tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False, default="")

    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dimensions), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
