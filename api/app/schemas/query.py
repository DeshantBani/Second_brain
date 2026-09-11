from datetime import datetime

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query_text: str
    source: str = "web"  # web | outlook | word


class RankedMatterOut(BaseModel):
    matter_id: str
    title: str
    client_name: str
    practice_area: str
    jurisdiction: str
    rank: int
    similarity_rationale: str
    confidence: str


class ReliabilityOutcomeOut(BaseModel):
    reliability_assessment_id: str | None
    authority_id: str
    citation: str
    court: str
    year: int
    relied_upon_for: str
    blocked_by_guardrail: bool
    guardrail_failure_reasons: list[str]
    verdict: str | None
    monitoring_status: str | None
    reasoning: str | None
    points_needing_fresh_work: list[dict]
    sources: list[dict]
    needs_review: bool
    reviewed_by_user_id: str | None
    reviewed_at: str | None


class QueryResultOut(BaseModel):
    query_log_id: str
    query_text: str
    no_confident_match: bool
    rationale: str
    degraded_mode: bool
    replayed_from_cache: bool = False
    query_fingerprint: dict | None
    ranked_matters: list[RankedMatterOut]
    top_matter: dict | None  # MatterDetail-shaped dict, kept loose to avoid duplicate schema drift
    comparison: dict | None
    reusability: dict | None
    reliability: list[ReliabilityOutcomeOut]


class ReviewRequest(BaseModel):
    reliability_assessment_id: str
    decision: str = "reviewed"  # reviewed | escalated


class QueryHistoryItem(BaseModel):
    query_log_id: str
    query_text: str
    source: str
    no_confident_match: bool
    degraded_mode: bool
    replayed_from_cache: bool
    blocked_by_guardrail: bool
    created_at: datetime


class AgentCallLogOut(BaseModel):
    id: str
    pipeline_run_id: str | None
    agent_name: str
    model: str
    cache_key: str
    system_instruction: str
    user_content: str
    raw_response_text: str | None
    success: bool
    replayed_from_cache: bool
    error_message: str | None
    duration_ms: int
    created_at: datetime
