from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_owner_session
from app.deps import CurrentUser, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_owner_session)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.id, user.email, user.role)
    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser = Depends(get_current_user)):
    return MeResponse(user_id=user.id, email=user.email, display_name=user.email.split("@")[0], role=user.role)
