from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from core.config import settings
from core.security import hash_password
from models.module_registry import ModuleRegistry
from models.organization import Organization
from models.user import User, UserRole


def verify_telnyx_signature(raw_body: bytes, request: Request) -> None:
    if not settings.TELNYX_REQUIRE_SIGNATURE:
        return
    signature = request.headers.get("telnyx-signature-ed25519")
    timestamp = request.headers.get("telnyx-timestamp")
    if not signature or not timestamp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telnyx signature")
    if not settings.TELNYX_PUBLIC_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telnyx public key")
    try:
        from nacl.encoding import Base64Encoder
        from nacl.signing import VerifyKey
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="PyNaCl is required for Telnyx signature verification",
        ) from exc
    try:
        verify_key = VerifyKey(settings.TELNYX_PUBLIC_KEY, encoder=Base64Encoder)
        signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}".encode("utf-8")
        verify_key.verify(signed_payload, Base64Encoder.decode(signature))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Telnyx signature: {exc}") from exc


def resolve_org(db: Session, payload: dict[str, Any]) -> Organization | None:
    metadata = payload.get("metadata") or {}
    org_id = metadata.get("org_id")
    if org_id:
        return db.query(Organization).filter(Organization.id == org_id).first()
    return db.query(Organization).order_by(Organization.id.asc()).first()


def module_enabled(db: Session, org_id: int) -> bool:
    module = (
        db.query(ModuleRegistry)
        .filter(ModuleRegistry.org_id == org_id, ModuleRegistry.module_key == "BILLING")
        .first()
    )
    return bool(module and module.enabled and not module.kill_switch)


def get_system_user(db: Session, org_id: int) -> User:
    user = db.query(User).filter(User.org_id == org_id, User.email == "system@fusonems.local").first()
    if user:
        return user
    user = User(
        org_id=org_id,
        email="system@fusonems.local",
        full_name="System Integration",
        hashed_password=hash_password("system"),
        role=UserRole.admin.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def require_telnyx_enabled() -> None:
    if not settings.TELNYX_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Telnyx integration is disabled. Set TELNYX_ENABLED=true.",
        )


def billing_users(db: Session, org_id: int) -> list[User]:
    # Limit to prevent performance issues - typically only a few billing users per org
    return db.query(User).filter(User.org_id == org_id, User.role == UserRole.billing.value).limit(100).all()
