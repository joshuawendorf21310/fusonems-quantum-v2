from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.auth import create_access_token, get_current_user, get_token_from_request, verify_password
from core.database import get_db
from models.session import Session as UserSession
from models.user import User
from utils.audit_log import record_audit_event


router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token, expires_at = create_access_token(
        subject=str(user.id),
        org_id=str(user.org_id),
        role=user.role,
    )
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    record_audit_event(
        db,
        org_id=str(user.org_id),
        user_id=str(user.id),
        action="USER_LOGIN",
        entity_type="session",
        entity_id=str(session.id),
        metadata={"userId": str(user.id)},
    )
    return LoginResponse(access_token=token)


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    token = get_token_from_request(request)
    session_query = db.query(UserSession).filter(UserSession.user_id == current_user.id)
    if token:
        session_query = session_query.filter(UserSession.token == token)
    session = session_query.first()
    if session:
        db.delete(session)
        db.commit()
        record_audit_event(
            db,
            org_id=str(current_user.org_id),
            user_id=str(current_user.id),
            action="USER_LOGOUT",
            entity_type="session",
            entity_id=str(session.id),
            metadata={"userId": str(current_user.id)},
        )
    return {"status": "ok"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "id": str(current_user.id),
        "orgId": str(current_user.org_id),
        "email": current_user.email,
        "role": current_user.role,
    }
