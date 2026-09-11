"""Minimal Office add-in auth bridge (see build plan Section 9: Outlook/Word are
scaffolded as route stubs this pass, not a full Office.js dialog/messageParent flow).
This reuses the exact same JWT auth as the main web app - an add-in user maps to the
same user_id and AccessGrant records, so the confidentiality gate is identical
regardless of surface."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_owner_session
from app.routers.auth import login
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/addin", tags=["addin"])


@router.post("/session", response_model=LoginResponse)
def addin_session(payload: LoginRequest, db: Session = Depends(get_owner_session)):
    """Stand-in for what a real Office dialog flow would call after the user signs in
    inside Office.context.ui.displayDialogAsync - identical credential check to
    /auth/login, returned in the same shape so the task pane can pass the token back
    via Office.context.ui.messageParent exactly as a real integration would."""
    return login(payload, db)
