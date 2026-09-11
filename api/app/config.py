"""Central configuration. Every environment variable the system uses is declared here -
nowhere else should call os.environ / os.getenv directly, so the .env.example file and
this class stay the single source of truth for what the app needs to run."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider (Gemini). Free-tier Gemini keys were verified during build to have
    # very little usable quota: Pro-tier models return 429 RESOURCE_EXHAUSTED
    # immediately, and the full "flash" model's free tier is only ~20 requests/day
    # (also verified live) - nowhere near enough for one full query (6-9 calls) plus
    # seeding. "flash-lite" variants carry a meaningfully higher free daily quota, so
    # both MODEL_FAST and MODEL_STRONG default there. Bump MODEL_STRONG to a Pro model
    # once on a paid key for better reasoning quality on the harder steps.
    gemini_api_key: str = ""
    model_fast: str = "gemini-flash-lite-latest"
    model_strong: str = "gemini-flash-lite-latest"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 1536

    # Case law reliability provider
    case_law_provider: str = "mock"
    indiankanoon_api_token: str = ""

    # Database
    database_url: str = "postgresql+psycopg://app_user:app_user_dev_password@localhost:5433/second_brain"
    database_url_owner: str = "postgresql+psycopg://sb_owner:sb_owner_dev_password@localhost:5433/second_brain"
    app_db_user: str = "app_user"
    app_db_password: str = "app_user_dev_password"
    postgres_user: str = "sb_owner"
    postgres_password: str = "sb_owner_dev_password"
    postgres_db: str = "second_brain"

    # Redis / Celery
    redis_url: str = "redis://localhost:6380/0"

    # MinIO - optional (see services/storage.py: nothing in the app ever reads a
    # document back from here, only writes a redundant copy). Defaults to "" so that
    # a deployment which simply never sets these (e.g. a hosted demo skipping object
    # storage entirely) is correctly detected as "not configured" and skips the write
    # immediately, rather than defaulting to a localhost address that doesn't exist
    # there and wasting a connection attempt on every document ingested.
    minio_endpoint: str = ""
    minio_public_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "second-brain-documents"
    minio_use_ssl: bool = False

    # Auth
    jwt_secret: str = "change-me-in-any-real-deployment-this-is-dev-only"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 1440

    @property
    def llm_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
