"""One-shot, idempotent schema bootstrap. Run via `make migrate`
(docker compose run --rm api python -m app.db_bootstrap).

Deliberately not Alembic for this pass (see build plan) - this script:
  1. creates the pgvector extension and the Postgres ENUM types our models reference
     (created with create_type=False so SQLAlchemy doesn't try to (re)create them itself),
  2. creates the non-superuser `app_user` role that Row-Level Security policies apply to,
  3. runs Base.metadata.create_all() to create every table,
  4. grants app_user exactly the privileges it needs on those tables,
  5. enables RLS and installs the AccessGrant-keyed isolation policies,
  6. creates the HNSW vector index on issue_fingerprints.embedding.

Every step is written to be safely re-run against an already-bootstrapped database.
"""
from sqlalchemy import text

from app.config import get_settings
from app.db import Base, owner_engine
import app.models  # noqa: F401 - registers all models on Base.metadata

settings = get_settings()

ENUM_TYPES = {
    "confidentiality_tier": ["tier1_confidential", "tier2_internal", "tier3_publishable"],
    "authority_status": ["good_law", "doubted", "distinguished", "overruled"],
    "monitoring_status": ["not_checked", "checked_clear", "checked_flagged"],
    "verdict": ["green", "amber", "red"],
}

# Tables keyed (directly or via matter_id) to a Matter, isolated by AccessGrant.
RLS_TABLES = ["matters", "documents", "issue_fingerprints", "matter_authority", "reliability_assessments"]


def create_enum_types(conn):
    for name, values in ENUM_TYPES.items():
        values_sql = ", ".join(f"'{v}'" for v in values)
        conn.execute(text(f"""
            DO $$ BEGIN
                CREATE TYPE {name} AS ENUM ({values_sql});
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """))


def create_app_role(conn):
    conn.execute(text(f"""
        DO $$ BEGIN
            CREATE ROLE {settings.app_db_user} LOGIN PASSWORD '{settings.app_db_password}' NOSUPERUSER NOCREATEDB NOCREATEROLE;
        EXCEPTION WHEN duplicate_object THEN
            EXECUTE format('ALTER ROLE %I WITH PASSWORD %L', '{settings.app_db_user}', '{settings.app_db_password}');
        END $$;
    """))
    conn.execute(text(f"GRANT CONNECT ON DATABASE {settings.postgres_db} TO {settings.app_db_user};"))
    conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {settings.app_db_user};"))


def grant_table_privileges(conn):
    conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {settings.app_db_user};"))
    conn.execute(text(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {settings.app_db_user};"))
    conn.execute(text(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {settings.app_db_user};"
    ))


def enable_rls(conn):
    # matters: the root policy - a user sees a matter iff they hold an access_grant for it.
    conn.execute(text("ALTER TABLE matters ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("DROP POLICY IF EXISTS matters_isolation ON matters;"))
    conn.execute(text("""
        CREATE POLICY matters_isolation ON matters
        USING (
            id IN (
                SELECT matter_id FROM access_grants
                WHERE user_id = current_setting('app.current_user_id', true)::uuid
            )
        );
    """))

    # everything else keyed to matter_id follows the identical pattern.
    for table in ["documents", "issue_fingerprints", "matter_authority", "reliability_assessments"]:
        conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        conn.execute(text(f"DROP POLICY IF EXISTS {table}_isolation ON {table};"))
        conn.execute(text(f"""
            CREATE POLICY {table}_isolation ON {table}
            USING (
                matter_id IN (
                    SELECT matter_id FROM access_grants
                    WHERE user_id = current_setting('app.current_user_id', true)::uuid
                )
            );
        """))


def create_vector_index(conn):
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS issue_fingerprints_embedding_hnsw_idx
        ON issue_fingerprints USING hnsw (embedding vector_cosine_ops);
    """))


def main():
    with owner_engine.begin() as conn:
        print("[db_bootstrap] creating pgvector extension...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        print("[db_bootstrap] creating enum types...")
        create_enum_types(conn)

        print("[db_bootstrap] creating app_user role...")
        create_app_role(conn)

    print("[db_bootstrap] creating tables (Base.metadata.create_all)...")
    Base.metadata.create_all(owner_engine)

    with owner_engine.begin() as conn:
        print("[db_bootstrap] granting table privileges to app_user...")
        grant_table_privileges(conn)

        print("[db_bootstrap] enabling row-level security...")
        enable_rls(conn)

        print("[db_bootstrap] creating vector index...")
        create_vector_index(conn)

    print("[db_bootstrap] done.")


if __name__ == "__main__":
    main()
