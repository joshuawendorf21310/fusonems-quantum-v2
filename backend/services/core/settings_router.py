from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.database import get_db
from models.setting import Setting
from models.user import User
from utils.audit_log import record_audit_event


router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingPayload(BaseModel):
    key: str
    value: dict[str, Any]


@router.get("")
def list_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    settings = (
        db.query(Setting)
        .filter(Setting.org_id == current_user.org_id)
        .all()
    )
    return {setting.key: setting.value for setting in settings}


@router.put("")
def upsert_setting(
    payload: SettingPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    setting = (
        db.query(Setting)
        .filter(
            Setting.org_id == current_user.org_id,
            Setting.key == payload.key,
        )
        .first()
    )
    if setting:
        setting.value = payload.value
        action = "SETTING_UPDATED"
    else:
        setting = Setting(
            org_id=current_user.org_id,
            key=payload.key,
            value=payload.value,
        )
        db.add(setting)
        action = "SETTING_CREATED"
    db.commit()
    record_audit_event(
        db,
        org_id=str(current_user.org_id),
        user_id=str(current_user.id),
        action=action,
        entity_type="setting",
        entity_id=str(setting.id),
        metadata={"key": payload.key},
    )
    return {"status": "ok"}
