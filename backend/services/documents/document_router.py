import hashlib
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.documents import DocumentRecord, DocumentTemplate
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/documents",
    tags=["Document Studio"],
    dependencies=[Depends(require_module("DOCUMENT_STUDIO"))],
)


class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    module_key: str
    template_version: str = "v1"
    status: str = "draft"
    jurisdiction: str = "default"
    sections: list[dict] = []
    classification: str = "NON_PHI"


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str
    module_key: str
    template_version: str
    status: str
    jurisdiction: str
    sections: list[dict]
    classification: str


class DocumentCreate(BaseModel):
    template_id: int
    title: str
    output_format: str = "PDF"
    content: dict = {}
    provenance: dict = {}
    classification: str = "NON_PHI"


class DocumentResponse(BaseModel):
    id: int
    title: str
    output_format: str
    status: str
    document_hash: str
    template_id: int
    classification: str
    created_at: Optional[str] = None


class TemplateActivate(BaseModel):
    status: str = "active"


@router.get("/templates", response_model=list[TemplateResponse])
def list_templates(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    return scoped_query(db, DocumentTemplate, user.org_id, request.state.training_mode).order_by(
        DocumentTemplate.module_key.asc()
    )


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    template = DocumentTemplate(**payload.dict(), org_id=user.org_id)
    apply_training_mode(template, request)
    db.add(template)
    db.commit()
    db.refresh(template)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="document_template",
        classification=payload.classification,
        after_state=model_snapshot(template),
        event_type="document_studio.template.created",
        event_payload={"template_id": template.id},
    )
    return template


@router.post("/templates/{template_id}/activate")
def activate_template(
    template_id: int,
    payload: TemplateActivate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    template = (
        scoped_query(db, DocumentTemplate, user.org_id, request.state.training_mode)
        .filter(DocumentTemplate.id == template_id)
        .first()
    )
    if not template:
        return {"status": "not_found"}
    before = model_snapshot(template)
    scoped_query(db, DocumentTemplate, user.org_id, request.state.training_mode).filter(
        DocumentTemplate.module_key == template.module_key,
        DocumentTemplate.id != template.id,
    ).update({DocumentTemplate.status: "deprecated"})
    template.status = payload.status
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="activate",
        resource="document_template",
        classification=template.classification,
        before_state=before,
        after_state=model_snapshot(template),
        event_type="document_studio.template.activated",
        event_payload={"template_id": template.id},
    )
    return {"status": "ok", "template_id": template.id}


@router.get("/records", response_model=list[DocumentResponse])
def list_documents(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    records = scoped_query(db, DocumentRecord, user.org_id, request.state.training_mode).order_by(
        DocumentRecord.created_at.desc()
    )
    return [
        DocumentResponse(
            id=record.id,
            title=record.title,
            output_format=record.output_format,
            status=record.status,
            document_hash=record.document_hash,
            template_id=record.template_id,
            classification=record.classification,
            created_at=record.created_at.isoformat() if record.created_at else None,
        )
        for record in records
    ]


@router.post("/records", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    template = (
        scoped_query(db, DocumentTemplate, user.org_id, request.state.training_mode)
        .filter(DocumentTemplate.id == payload.template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Template not found")
    document_hash = hashlib.sha256(str(payload.content).encode("utf-8")).hexdigest()
    record = DocumentRecord(
        org_id=user.org_id,
        template_id=payload.template_id,
        title=payload.title,
        output_format=payload.output_format,
        content=payload.content,
        provenance=payload.provenance,
        document_hash=document_hash,
        classification=payload.classification,
        created_by=user.id,
    )
    apply_training_mode(record, request)
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="document_record",
        classification=payload.classification,
        after_state=model_snapshot(record),
        event_type="document_studio.record.created",
        event_payload={"document_id": record.id},
    )
    return DocumentResponse(
        id=record.id,
        title=record.title,
        output_format=record.output_format,
        status=record.status,
        document_hash=record.document_hash,
        template_id=record.template_id,
        classification=record.classification,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )


@router.post("/records/{record_id}/finalize")
def finalize_document(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.medical_director, UserRole.founder)),
):
    record = (
        scoped_query(db, DocumentRecord, user.org_id, request.state.training_mode)
        .filter(DocumentRecord.id == record_id)
        .first()
    )
    if not record:
        return {"status": "not_found"}
    before = model_snapshot(record)
    record.status = "final"
    record.document_hash = hashlib.sha256(str(record.content).encode("utf-8")).hexdigest()
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="finalize",
        resource="document_record",
        classification=record.classification,
        before_state=before,
        after_state=model_snapshot(record),
        event_type="document_studio.record.finalized",
        event_payload={"document_id": record.id},
    )
    return {"status": "ok", "document_id": record.id}
