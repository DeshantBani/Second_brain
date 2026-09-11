import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

VerdictEnum = PGEnum("green", "amber", "red", name="verdict", create_type=False)


class ReliabilityAssessment(Base):
    """RLS-protected via matter_id. The reliability layer's product: a graded,
    reasoned, source-logged verdict - never a bare "cleared" signal. Rows persist even
    when a background recheck later flips the underlying Authority's status (`stale`
    is set instead of deleting), because every past assessment must remain auditable."""

    __tablename__ = "reliability_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    query_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("query_logs.id"), nullable=True)
    authority_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("authorities.id"), nullable=False)

    verdict: Mapped[str | None] = mapped_column(VerdictEnum, nullable=True)  # null == withheld by guardrail
    blocked_by_guardrail: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guardrail_failure_reasons: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    points_needing_fresh_work: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)

    stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
