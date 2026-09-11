from datetime import datetime

from pydantic import BaseModel, field_validator


class AuthorityOut(BaseModel):
    id: str
    citation: str
    court: str
    year: int
    status: str
    monitoring_status: str
    last_checked_at: datetime | None
    provider_source: str
    treatment_history: list

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v):
        return str(v)


class RecheckResponse(BaseModel):
    authority: AuthorityOut
    status_changed: bool
    flagged_assessment_ids: list[str]


class AuditLogOut(BaseModel):
    id: str
    pipeline_run_id: str | None
    user_email: str
    source: str
    query_text: str
    no_confident_match: bool
    degraded_mode: bool
    replayed_from_cache: bool
    blocked_by_guardrail: bool
    created_at: datetime


class HealthOut(BaseModel):
    status: str
    llm_configured: bool
    llm_provider: str
    case_law_provider: str
    db_ok: bool
