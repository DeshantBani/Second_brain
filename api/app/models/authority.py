import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

AuthorityStatusEnum = PGEnum(
    "good_law", "doubted", "distinguished", "overruled",
    name="authority_status", create_type=False,
)

MonitoringStatusEnum = PGEnum(
    "not_checked", "checked_clear", "checked_flagged",
    name="monitoring_status", create_type=False,
)


class Authority(Base):
    """NOT row-level-secured - case law is not matter-confidential, it's public legal
    fact. `monitoring_status` is intentionally a 3-state field, not a boolean flag:
    the absence of a flag must never be presented as "checked and clear" when in fact
    nothing has been checked at all."""

    __tablename__ = "authorities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citation: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    court: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(AuthorityStatusEnum, nullable=False, default="good_law")
    treatment_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monitoring_status: Mapped[str] = mapped_column(MonitoringStatusEnum, nullable=False, default="not_checked")
    provider_source: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
