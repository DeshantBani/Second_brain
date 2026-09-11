from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.deps import CurrentUser, get_current_user, get_db
from app.models.querylog import QueryLog
from app.models.reliability import ReliabilityAssessment
from app.schemas.query import QueryRequest, QueryResultOut, ReviewRequest
from app.services.orchestrator import run_query_pipeline

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResultOut)
async def submit_query(payload: QueryRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not payload.query_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query_text must not be empty")
    result = await run_query_pipeline(db, user.id, payload.query_text, payload.source)
    return QueryResultOut(**result)


@router.get("/{query_log_id}", response_model=QueryResultOut)
def get_query(query_log_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    log = db.get(QueryLog, query_log_id)
    if log is None or str(log.user_id) != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")
    if log.full_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No stored result for this query")
    payload = dict(log.full_result)
    payload["query_log_id"] = str(log.id)
    return QueryResultOut(**payload)


@router.post("/{query_log_id}/review")
def review_assessment(query_log_id: str, payload: ReviewRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """The mandatory human-verification gate: recording that a lawyer has actually
    looked at the underlying sources before a reliability verdict (or any cited text)
    is used downstream. This does not change the verdict - it only records review."""
    log = db.get(QueryLog, query_log_id)
    if log is None or str(log.user_id) != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")

    assessment = db.get(ReliabilityAssessment, payload.reliability_assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reliability assessment not found")

    assessment.reviewed_by_user_id = user.id
    assessment.reviewed_at = datetime.now(timezone.utc)
    assessment.review_decision = payload.decision
    assessment.needs_review = False

    # Keep QueryLog.full_result (what GET /query/{id} serves back, e.g. after a page
    # refresh) in sync with the review, not just the ReliabilityAssessment row itself -
    # otherwise a refreshed page would show the review as never having happened.
    if log.full_result and isinstance(log.full_result.get("reliability"), list):
        for outcome in log.full_result["reliability"]:
            if outcome.get("reliability_assessment_id") == str(assessment.id):
                outcome["reviewed_by_user_id"] = str(assessment.reviewed_by_user_id)
                outcome["reviewed_at"] = assessment.reviewed_at.isoformat()
                outcome["needs_review"] = False
        flag_modified(log, "full_result")

    db.flush()
    return {
        "reliability_assessment_id": str(assessment.id),
        "reviewed_by_user_id": str(assessment.reviewed_by_user_id),
        "reviewed_at": assessment.reviewed_at.isoformat(),
        "review_decision": assessment.review_decision,
    }
