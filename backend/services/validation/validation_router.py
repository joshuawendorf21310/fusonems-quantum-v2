from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.user import User, UserRole
from models.validation import DataValidationIssue, ValidationRule
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/validation",
    tags=["Validation"],
    dependencies=[Depends(require_module("VALIDATION"))],
)


class ValidationScan(BaseModel):
    entity_type: str
    entity_id: str
    patient_name: str | None = None
    date_of_birth: str | None = None
    insurance_id: str | None = None
    encounter_code: str | None = None
    claim_amount: float | None = None


class RuleCreate(BaseModel):
    name: str
    entity_type: str
    rule_type: str = "required_field"
    field: str = ""
    condition: dict = {}
    severity: str = "High"
    enforcement: str = "hard_block"
    status: str = "active"
    version: str = "v1"
    description: str = ""


class RuleUpdate(BaseModel):
    name: str | None = None
    rule_type: str | None = None
    field: str | None = None
    condition: dict | None = None
    severity: str | None = None
    enforcement: str | None = None
    status: str | None = None
    version: str | None = None
    description: str | None = None


class RuleTest(BaseModel):
    entity_type: str
    payload: dict


@router.post("/scan", status_code=status.HTTP_201_CREATED)
def scan_payload(
    payload: ValidationScan,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider)),
):
    issues = []
    if not payload.patient_name:
        issues.append("Missing patient name")
    if not payload.date_of_birth:
        issues.append("Missing date of birth")
    if not payload.insurance_id:
        issues.append("Missing insurance ID")
    if not payload.encounter_code:
        issues.append("Missing encounter code")
    if payload.claim_amount is not None and payload.claim_amount <= 0:
        issues.append("Claim amount must be greater than zero")

    stored = []
    for issue in issues:
        record = DataValidationIssue(
            org_id=user.org_id,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            severity="High" if "Missing" in issue else "Medium",
            issue=issue,
        )
        apply_training_mode(record, request)
        db.add(record)
        stored.append(record)

    db.commit()
    for record in stored:
        audit_and_event(
            db=db,
            request=request,
            user=user,
            action="create",
            resource="validation_issue",
            classification=record.classification,
            after_state=model_snapshot(record),
            event_type="validation.issue.created",
            event_payload={"issue_id": record.id},
        )
    return {"issues": issues, "count": len(issues)}


@router.get("/issues")
def list_issues(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    return scoped_query(
        db, DataValidationIssue, user.org_id, request.state.training_mode
    ).order_by(DataValidationIssue.created_at.desc()).all()


@router.get("/rules")
def list_rules(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    rules = scoped_query(db, ValidationRule, user.org_id, request.state.training_mode).order_by(
        ValidationRule.created_at.desc()
    )
    return [model_snapshot(rule) for rule in rules]


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: RuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    rule = ValidationRule(org_id=user.org_id, **payload.model_dump())
    apply_training_mode(rule, request)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="validation_rule",
        classification=rule.classification,
        after_state=model_snapshot(rule),
        event_type="validation.rule.created",
        event_payload={"rule_id": rule.id},
    )
    return model_snapshot(rule)


@router.patch("/rules/{rule_id}")
def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    rule = (
        scoped_query(db, ValidationRule, user.org_id, request.state.training_mode)
        .filter(ValidationRule.id == rule_id)
        .first()
    )
    if not rule:
        return {"status": "not_found"}
    before = model_snapshot(rule)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(rule, key, value)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="validation_rule",
        classification=rule.classification,
        before_state=before,
        after_state=model_snapshot(rule),
        event_type="validation.rule.updated",
        event_payload={"rule_id": rule.id},
    )
    return model_snapshot(rule)


@router.post("/rules/test")
def test_rules(
    payload: RuleTest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    rules = scoped_query(db, ValidationRule, user.org_id, request.state.training_mode).filter(
        ValidationRule.entity_type == payload.entity_type,
        ValidationRule.status == "active",
    ).all()
    findings = []
    for rule in rules:
        if rule.rule_type == "required_field":
            if not payload.payload.get(rule.field):
                findings.append({"rule": rule.name, "issue": f"Missing {rule.field}", "severity": rule.severity})
        if rule.rule_type == "conditional":
            condition = rule.condition or {}
            if_field = condition.get("if_field")
            if_value = condition.get("if_value")
            then_field = condition.get("then_field")
            if if_field and payload.payload.get(if_field) == if_value and not payload.payload.get(then_field):
                findings.append(
                    {"rule": rule.name, "issue": f"Missing {then_field}", "severity": rule.severity}
                )
    return {"count": len(findings), "issues": findings}
