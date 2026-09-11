from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_current_user, get_db
from app.models.drafting_session import DraftingSession
from app.models.proofreading_report import ProofreadingReport
from app.schemas.drafting import (
    AddDraftingMessageRequest,
    CreateDraftingSessionRequest,
    DraftingSessionOut,
    DraftingSessionSummary,
    ProofreadingReportOut,
    ProofreadingReportSummary,
    ProofreadRequest,
)
from app.services.drafting_service import add_message, create_drafting_session, generate_draft
from app.services.proofreading_service import run_proofreading

router = APIRouter(tags=["drafting"])


def _session_out(session: DraftingSession) -> DraftingSessionOut:
    return DraftingSessionOut(
        id=str(session.id), case_brief=session.case_brief, status=session.status,
        conversation=session.conversation, gathered_requirements=session.gathered_requirements,
        template_structure=session.template_structure, draft_sections=session.draft_sections,
        degraded_mode=session.degraded_mode, created_at=session.created_at, updated_at=session.updated_at,
    )


def _get_owned_session(db: Session, session_id: str, user: CurrentUser) -> DraftingSession:
    session = db.get(DraftingSession, session_id)
    if session is None or str(session.user_id) != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drafting session not found")
    return session


@router.post("/drafting/sessions", response_model=DraftingSessionOut)
async def start_drafting_session(payload: CreateDraftingSessionRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not payload.case_brief.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="case_brief must not be empty")
    session = await create_drafting_session(db, user.id, payload.case_brief)
    return _session_out(session)


@router.get("/drafting/sessions", response_model=list[DraftingSessionSummary])
def list_drafting_sessions(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(DraftingSession).where(DraftingSession.user_id == user.id).order_by(DraftingSession.updated_at.desc()).limit(100)
    ).scalars().all()
    return [
        DraftingSessionSummary(id=str(r.id), case_brief=r.case_brief, status=r.status, created_at=r.created_at, updated_at=r.updated_at)
        for r in rows
    ]


@router.get("/drafting/sessions/{session_id}", response_model=DraftingSessionOut)
def get_drafting_session(session_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _session_out(_get_owned_session(db, session_id, user))


@router.post("/drafting/sessions/{session_id}/messages", response_model=DraftingSessionOut)
async def send_drafting_message(session_id: str, payload: AddDraftingMessageRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(db, session_id, user)
    if session.status != "gathering":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This session is no longer gathering requirements")
    if not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message must not be empty")
    session = await add_message(db, session, payload.message)
    return _session_out(session)


@router.post("/drafting/sessions/{session_id}/draft", response_model=DraftingSessionOut)
async def generate_drafting_draft(session_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(db, session_id, user)
    if session.status not in ("ready", "drafted"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This session has not gathered enough requirements yet")
    session = await generate_draft(db, session)
    return _session_out(session)


@router.post("/proofread", response_model=ProofreadingReportOut)
async def proofread(payload: ProofreadRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not payload.draft_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="draft_text must not be empty")
    report = await run_proofreading(db, user.id, payload.draft_text, payload.case_brief)
    return ProofreadingReportOut(
        id=str(report.id), case_brief=report.case_brief, draft_text=report.draft_text, summary=report.summary,
        findings=report.findings, degraded_mode=report.degraded_mode, created_at=report.created_at,
    )


@router.get("/proofread", response_model=list[ProofreadingReportSummary])
def list_proofreading_reports(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(ProofreadingReport).where(ProofreadingReport.user_id == user.id).order_by(ProofreadingReport.created_at.desc()).limit(100)
    ).scalars().all()
    return [
        ProofreadingReportSummary(id=str(r.id), summary=r.summary, finding_count=len(r.findings), created_at=r.created_at)
        for r in rows
    ]


@router.get("/proofread/{report_id}", response_model=ProofreadingReportOut)
def get_proofreading_report(report_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.get(ProofreadingReport, report_id)
    if report is None or str(report.user_id) != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ProofreadingReportOut(
        id=str(report.id), case_brief=report.case_brief, draft_text=report.draft_text, summary=report.summary,
        findings=report.findings, degraded_mode=report.degraded_mode, created_at=report.created_at,
    )
