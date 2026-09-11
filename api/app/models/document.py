import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

ConfidentialityTier = PGEnum(
    "tier1_confidential", "tier2_internal", "tier3_publishable",
    name="confidentiality_tier", create_type=False,
)


class Document(Base):
    """RLS-protected via matter_id. `page_map` is a list of
    {page, paragraph, text} objects that lets every downstream agent claim point back
    to an exact quoted location - the backbone of the "never assert without a source" rule."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)  # memo | email | contract | pleading | due_diligence | note
    confidentiality_tier: Mapped[str] = mapped_column(ConfidentialityTier, nullable=False, default="tier1_confidential")
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="text/markdown")
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page_map: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
