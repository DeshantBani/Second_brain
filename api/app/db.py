"""SQLAlchemy engine/session setup.

Two engines exist on purpose:
- `owner_engine` connects as the Postgres owner role and BYPASSES row-level security.
  Only migrations (db_bootstrap) and the seed script use it.
- `engine` (the runtime engine) connects as `app_user`, a non-superuser role that RLS
  policies apply to. Every request-scoped session sets `app.current_user_id` via
  `SET LOCAL` so Postgres itself enforces matter-level access control - see deps.py.
"""
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
owner_engine = create_engine(settings.database_url_owner, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
OwnerSessionLocal = sessionmaker(bind=owner_engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_owner_session() -> Generator[Session, None, None]:
    """RLS-bypassing session, for migrations/seed/admin tooling only."""
    db = OwnerSessionLocal()
    try:
        yield db
    finally:
        db.close()


def scoped_session_for_user(user_id: str | None) -> Session:
    """Runtime, RLS-enforced session with app.current_user_id set for the transaction.

    When user_id is None (e.g. an unauthenticated health check) the session still runs
    as app_user, which owns zero rows under any RLS policy - it simply sees nothing.

    Postgres's SET/SET LOCAL do not accept bind parameters ($1-style placeholders) -
    only literals. set_config() is a regular function and does, so it's the safe way
    to parameterize this per-request value; its third argument (true) scopes the
    setting to the current transaction, exactly like SET LOCAL.
    """
    db = SessionLocal()
    effective_id = user_id or "00000000-0000-0000-0000-000000000000"
    db.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": effective_id})
    return db
