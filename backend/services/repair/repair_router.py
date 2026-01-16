from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_hems_db
from core.guards import require_module
from core.security import require_roles
from models.exports import OrphanRepairAction
from models.hems import HemsAssignment, HemsMission
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/repair",
    tags=["Repair"],
    dependencies=[Depends(require_module("REPAIR"))],
)


class RepairAction(BaseModel):
    orphan_type: str
    orphan_id: int
    action: str
    new_mission_id: int | None = None


@router.get("/scan")
def scan_orphans(
    request: Request,
    hems_db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    assignments = scoped_query(
        hems_db, HemsAssignment, user.org_id, request.state.training_mode
    ).all()
    orphans = []
    for assignment in assignments:
        mission = (
            scoped_query(hems_db, HemsMission, user.org_id, request.state.training_mode)
            .filter(HemsMission.id == assignment.mission_id)
            .first()
        )
        if not mission:
            orphans.append(
                {
                    "orphan_type": "hems_assignment",
                    "orphan_id": assignment.id,
                    "mission_id": assignment.mission_id,
                    "crew_id": assignment.crew_id,
                    "aircraft_id": assignment.aircraft_id,
                }
            )
    return {"orphans": orphans, "count": len(orphans)}


@router.post("/resolve", status_code=status.HTTP_200_OK)
def resolve_orphan(
    payload: RepairAction,
    request: Request,
    hems_db: Session = Depends(get_hems_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    if payload.orphan_type != "hems_assignment":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported orphan type")

    assignment = scoped_query(
        hems_db, HemsAssignment, user.org_id, request.state.training_mode
    ).filter(HemsAssignment.id == payload.orphan_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orphan not found")

    before = model_snapshot(assignment)
    if payload.action == "relink" and payload.new_mission_id:
        mission = scoped_query(
            hems_db, HemsMission, user.org_id, request.state.training_mode
        ).filter(HemsMission.id == payload.new_mission_id).first()
        if not mission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
        assignment.mission_id = mission.id
        hems_db.commit()
    elif payload.action == "mark_detached":
        hems_db.commit()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    action = OrphanRepairAction(
        org_id=user.org_id,
        orphan_type=payload.orphan_type,
        orphan_id=str(payload.orphan_id),
        action=payload.action,
        details={"new_mission_id": payload.new_mission_id},
    )
    apply_training_mode(action, request)
    hems_db.add(action)
    hems_db.commit()
    hems_db.refresh(action)
    audit_and_event(
        db=hems_db,
        request=request,
        user=user,
        action="repair",
        resource="orphan_repair",
        classification=action.classification,
        before_state=before,
        after_state=model_snapshot(assignment),
        event_type="repair.orphan.resolved",
        event_payload={"repair_id": action.id},
        schema_name="hems",
    )
    return {"status": "resolved", "repair_id": action.id}
