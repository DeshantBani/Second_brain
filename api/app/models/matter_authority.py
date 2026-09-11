import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MatterAuthority(Base):
    """RLS-protected via matter_id. Join table recording which of a matter's documents
    relied on which Authority, and exactly where - this is what lets the reliability
    agent be pointed at "the authorities THIS matter actually used"."""

    __tablename__ = "matter_authority"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    authority_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("authorities.id", ondelete="CASCADE"), nullable=False, index=True)
    cited_in_document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    cited_at_page: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cited_at_paragraph: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    relied_upon_for: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
