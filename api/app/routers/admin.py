from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_db, require_admin
from app.models.agent_call_log import AgentCallLog
from app.models.authority import Authority
from app.models.querylog import QueryLog
from app.models.reliability import ReliabilityAssessment
from app.models.user import User
from app.reliability.factory import get_case_law_provider
from app.schemas.admin import AuditLogOut, AuthorityOut, RecheckResponse
from app.schemas.query import AgentCallLogOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/authorities", response_model=list[AuthorityOut])
def list_authorities(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(select(Authority).order_by(Authority.citation)).scalars().all()
    return [AuthorityOut.model_validate(r) for r in rows]


@router.post("/authorities/{authority_id}/recheck", response_model=RecheckResponse)
def recheck_authority(authority_id: str, user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    """Manually trigger what jobs/monitor.py does on a schedule: re-check one
    Authority against the active CaseLawProvider and flag any dependent
    ReliabilityAssessment as needing review if its status has moved."""
    authority = db.get(Authority, authority_id)
    if authority is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authority not found")

    provider = get_case_law_provider()
    live = provider.get_citation_status(authority.citation)

    status_changed = live.status != authority.status
    authority.status = live.status
    authority.treatment_history = [e.model_dump(mode="json") for e in live.treatment_history]
    authority.last_checked_at = datetime.now(timezone.utc)
    authority.monitoring_status = "checked_flagged" if live.treatment_history else "checked_clear"

    flagged_ids: list[str] = []
    if status_changed:
        dependents = db.execute(
            select(ReliabilityAssessment).where(ReliabilityAssessment.authority_id == authority_id)
        ).scalars().all()
        for dep in dependents:
            dep.needs_review = True
            dep.stale = True
            flagged_ids.append(str(dep.id))

    db.flush()
    return RecheckResponse(authority=AuthorityOut.model_validate(authority), status_changed=status_changed, flagged_assessment_ids=flagged_ids)


@router.get("/audit", response_model=list[AuditLogOut])
def list_audit_log(user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(
        select(QueryLog, User).join(User, User.id == QueryLog.user_id).order_by(QueryLog.created_at.desc()).limit(200)
    ).all()
    return [
        AuditLogOut(
            id=str(log.id), pipeline_run_id=log.pipeline_run_id, user_email=u.email, source=log.source,
            query_text=log.query_text, no_confident_match=log.no_confident_match, degraded_mode=log.degraded_mode,
            replayed_from_cache=log.replayed_from_cache, blocked_by_guardrail=log.blocked_by_guardrail,
            created_at=log.created_at,
        )
        for log, u in rows
    ]


@router.get("/agent-calls", response_model=list[AgentCallLogOut])
def list_agent_calls(
    pipeline_run_id: str | None = None,
    agent_name: str | None = None,
    user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """The raw call log: every request sent to and response received from Gemini
    (structured-output generations and embeddings alike), across the whole system -
    the "whole log system" for inspecting exactly what the model saw and said, and for
    seeing which calls were served live vs. replayed from a cached prior response."""
    query = select(AgentCallLog).order_by(AgentCallLog.created_at.desc()).limit(300)
    if pipeline_run_id:
        query = query.where(AgentCallLog.pipeline_run_id == pipeline_run_id)
    if agent_name:
        query = query.where(AgentCallLog.agent_name == agent_name)
    rows = db.execute(query).scalars().all()
    return [
        AgentCallLogOut(
            id=str(r.id), pipeline_run_id=r.pipeline_run_id, agent_name=r.agent_name, model=r.model,
            cache_key=r.cache_key, system_instruction=r.system_instruction, user_content=r.user_content,
            raw_response_text=r.raw_response_text, success=r.success, replayed_from_cache=r.replayed_from_cache,
            error_message=r.error_message, duration_ms=r.duration_ms, created_at=r.created_at,
        )
        for r in rows
    ]
