import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DraftingSession(Base):
    """A standalone (not matter-linked) drafting workspace: the lawyer supplies a free-
    text case brief, the drafting-intake agent asks clarifying questions turn by turn
    (nature of petition, grounds, relief sought, forum, parties) until it has enough to
    draft, then the drafting agent produces the petition using the case brief plus a
    template structure the web-research step found. NOT row-level-secured like the
    matter archive - scoped by user_id ownership only, same pattern as QueryLog, since
    this is a personal workspace rather than a shared, access-granted archive."""

    __tablename__ = "drafting_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    case_brief: Mapped[str] = mapped_column(Text, nullable=False)
    # status: gathering (intake agent still asking questions) | ready (enough info
    # gathered, draft not yet generated) | drafted (final draft produced)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="gathering")

    # [{role: "assistant"|"user", content: str, at: iso-timestamp}, ...]
    conversation: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Set once the intake agent signals ready_to_draft=true - see DraftingIntakeResult.
    gathered_requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # The web-research agent's derived section structure + source URLs, set when the
    # draft is generated.
    template_structure: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # [{section_name, content}, ...] - the actual generated petition, section by section.
    draft_sections: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    degraded_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
