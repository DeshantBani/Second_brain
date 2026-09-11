"""Every query, from every surface, lands in QueryLog - this is the audit trail the
non-negotiable constraints require ("every reliability assessment is logged with its
reasoning and its sources"; "audit everything")."""
from sqlalchemy.orm import Session

from app.models.querylog import QueryLog


def log_query(
    db: Session,
    user_id: str,
    source: str,
    query_text: str,
    query_fingerprint: dict | None,
    matter_access_scope: list,
    results_returned: list,
    sources_cited: list,
    no_confident_match: bool = False,
    degraded_mode: bool = False,
    blocked_by_guardrail: bool = False,
    full_result: dict | None = None,
    pipeline_run_id: str | None = None,
    replayed_from_cache: bool = False,
) -> QueryLog:
    log = QueryLog(
        user_id=user_id,
        source=source,
        query_text=query_text,
        query_fingerprint=query_fingerprint,
        matter_access_scope=matter_access_scope,
        results_returned=results_returned,
        sources_cited=sources_cited,
        no_confident_match=no_confident_match,
        degraded_mode=degraded_mode,
        blocked_by_guardrail=blocked_by_guardrail,
        full_result=full_result,
        pipeline_run_id=pipeline_run_id,
        replayed_from_cache=replayed_from_cache,
    )
    db.add(log)
    db.flush()
    return log
