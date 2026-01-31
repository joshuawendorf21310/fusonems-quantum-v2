import hashlib
import hmac
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from core.config import settings
from models.legal import LegalHold
from models.quantum_documents import (
    DiscoveryExport,
    DocumentFile,
    DocumentFolder,
    DocumentPermission,
    DocumentVersion,
    RetentionPolicy,
)
from models.user import User, UserRole
from utils.legal import get_active_hold
from utils.storage import build_storage_key, get_storage_backend
from utils.tenancy import scoped_query
from utils.decision import DecisionBuilder, finalize_decision_packet
from utils.events import event_bus
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/documents",
    tags=["Quantum Documents"],
    dependencies=[Depends(require_module("DOCUMENT_STUDIO"))],
)


def _has_permission(
    db: Session,
    user: User,
    resource_type: str,
    resource_id: str,
    permission: str,
) -> bool:
    if user.role in {UserRole.admin.value, UserRole.founder.value, UserRole.medical_director.value}:
        return True
    query = (
        db.query(DocumentPermission)
        .filter(
            DocumentPermission.org_id == user.org_id,
            DocumentPermission.resource_type == resource_type,
            DocumentPermission.resource_id == resource_id,
            DocumentPermission.permission == permission,
        )
    )
    return (
        query.filter(
            (DocumentPermission.subject_type == "user")
            & (DocumentPermission.subject_id == user.id)
        ).first()
        is not None
        or query.filter(
            (DocumentPermission.subject_type == "role")
            & (DocumentPermission.subject_key == user.role)
        ).first()
        is not None
    )


def _retention_blocked(policy: RetentionPolicy | None, created_at: datetime | None) -> bool:
    if not policy or policy.retention_days is None or created_at is None:
        return False
    created_at_aware = created_at.replace(tzinfo=timezone.utc)
    return created_at_aware + timedelta(days=policy.retention_days) > datetime.now(timezone.utc)


def _legal_hold_count(db: Session, org_id: int, file_id: str) -> int:
    return (
        db.query(LegalHold)
        .filter(
            LegalHold.org_id == org_id,
            LegalHold.scope_type == "document_file",
            LegalHold.scope_id == file_id,
            LegalHold.status == "Active",
        )
        .count()
    )


def _serialize_file(file: DocumentFile, legal_hold_count: int, policy: RetentionPolicy | None) -> dict:
    data = model_snapshot(file)
    data["legal_hold_count"] = legal_hold_count
    if policy:
        data["retention_policy"] = {
            "id": policy.id,
            "name": policy.name,
            "retention_days": policy.retention_days,
        }
    data["download_url"] = _signed_download_url(file.id, file.org_id)
    return data


def _signed_download_url(file_id: str, org_id: int) -> str:
    expires = int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
    signature = _sign_download(file_id, org_id, expires)
    return f"/api/documents/files/{file_id}/download?expires={expires}&signature={signature}"


def _sign_download(file_id: str, org_id: int, expires: int) -> str:
    payload = f"{file_id}:{org_id}:{expires}".encode("utf-8")
    digest = hmac.new(settings.DOCS_ENCRYPTION_KEY.encode("utf-8"), payload, hashlib.sha256)
    return digest.hexdigest()


def _verify_signature(file_id: str, org_id: int, expires: int, signature: str) -> bool:
    if expires < int(datetime.now(timezone.utc).timestamp()):
        return False
    expected = _sign_download(file_id, org_id, expires)
    return hmac.compare_digest(expected, signature)


def _policy_decision(
    db: Session,
    request: Request,
    user: User,
    doc: DocumentFile,
    action: str,
    policy: RetentionPolicy | None = None,
    hold: LegalHold | None = None,
) -> dict:
    builder = DecisionBuilder(component="documents_policy", component_version="v1")
    input_payload = {
        "file_id": doc.id,
        "action": action,
        "retention_policy_id": policy.id if policy else None,
        "legal_hold_id": hold.id if hold else None,
        "status": doc.status,
    }
    file_ref = builder.add_evidence("document_file", f"document:{doc.id}", {"classification": doc.classification})
    if hold:
        hold_ref = builder.add_evidence("legal_hold", f"hold:{hold.id}", {"scope": hold.scope_type})
        builder.add_reason(
            "DOC.LEGAL_HOLD.BLOCK_DELETE.v1",
            "Legal hold is active. Deletion or mutation is frozen.",
            severity="High",
            decision="BLOCK",
            evidence_refs=[file_ref, hold_ref],
        )
        builder.add_next_action(
            "request_release",
            "Request legal hold release",
            f"/api/legal/holds/{hold.id}/request_release",
            "legal",
        )
    if policy and _retention_blocked(policy, doc.created_at):
        policy_ref = builder.add_evidence(
            "retention_policy",
            f"policy:{policy.id}",
            {"retention_days": policy.retention_days},
        )
        builder.add_reason(
            "DOC.RETENTION.BLOCK_DELETE.v1",
            "Retention period has not expired.",
            severity="High",
            decision="BLOCK",
            evidence_refs=[file_ref, policy_ref],
        )
        builder.add_next_action(
            "export_discovery",
            "Create discovery export instead",
            "/api/documents/exports/discovery",
            "admin",
        )
    if not builder.reasons:
        builder.add_reason(
            "DOC.ACTION.ALLOW.v1",
            "Policy checks passed.",
            severity="Low",
            decision="ALLOW",
            evidence_refs=[file_ref],
        )
    decision = finalize_decision_packet(
        db=db,
        request=request,
        user=user,
        builder=builder,
        input_payload=input_payload,
        classification=doc.classification,
        action=f"{action}_policy_check",
        resource="documents_file",
        reason_code="SMART_POLICY",
    )
    if decision["decision"] == "BLOCK":
        event_bus.publish(
            db=db,
            org_id=user.org_id,
            event_type=f"documents.file.{action}_blocked",
            payload={
                "file_id": doc.id,
                "action": action,
                "reason_codes": decision.get("rule_ids", []),
            },
            actor_id=user.id,
            actor_role=user.role,
            device_id=request.headers.get("x-device-id", ""),
            server_time=getattr(request.state, "server_time", None),
            drift_seconds=getattr(request.state, "drift_seconds", 0),
            drifted=getattr(request.state, "drifted", False),
            training_mode=getattr(request.state, "training_mode", False),
        )
    return decision


@router.get("/folders")
def list_folders(
    request: Request,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, DocumentFolder, user.org_id, request.state.training_mode)
    if parent_id:
        query = query.filter(DocumentFolder.parent_id == parent_id)
    return query.order_by(DocumentFolder.name.asc()).all()


@router.post("/folders", status_code=status.HTTP_201_CREATED)
def create_folder(
    name: str = Form(...),
    parent_id: Optional[str] = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.billing)),
):
    slug = name.strip().lower().replace(" ", "-")
    folder = DocumentFolder(
        org_id=user.org_id,
        parent_id=parent_id,
        name=name,
        path_slug=slug,
        created_by=user.id,
    )
    apply_training_mode(folder, request)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="documents_folder",
        classification="OPS",
        after_state=model_snapshot(folder),
        event_type="documents.folder.created",
        event_payload={"folder_id": folder.id},
    )
    return folder


@router.patch("/folders/{folder_id}")
def update_folder(
    folder_id: str,
    name: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.billing)),
):
    folder = (
        scoped_query(db, DocumentFolder, user.org_id, request.state.training_mode)
        .filter(DocumentFolder.id == folder_id)
        .first()
    )
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    before = model_snapshot(folder)
    folder.name = name
    folder.path_slug = name.strip().lower().replace(" ", "-")
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="update",
        resource="documents_folder",
        classification="OPS",
        before_state=before,
        after_state=model_snapshot(folder),
        event_type="documents.folder.updated",
        event_payload={"folder_id": folder.id},
    )
    return folder


@router.get("/files")
def list_files(
    request: Request,
    folder_id: Optional[str] = None,
    q: Optional[str] = None,
    classification: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    query = scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
    if folder_id:
        query = query.filter(DocumentFile.folder_id == folder_id)
    if classification:
        query = query.filter(DocumentFile.classification == classification)
    if q:
        query = query.filter(DocumentFile.filename.ilike(f"%{q}%"))
    results = query.order_by(DocumentFile.created_at.desc()).all()
    if tag:
        results = [doc for doc in results if tag in (doc.tags or [])]
    policies = {
        policy.id: policy
        for policy in scoped_query(db, RetentionPolicy, user.org_id, request.state.training_mode).all()
    }
    return [
        _serialize_file(doc, _legal_hold_count(db, user.org_id, doc.id), policies.get(doc.retention_policy_id))
        for doc in results
    ]


@router.post("/files", status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    classification: str = Form("ops"),
    retention_policy_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.billing)),
):
    file_id = str(uuid4())
    storage_key = build_storage_key(user.org_id, f"{file_id}/{file.filename}")
    try:
        raw = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    digest = hashlib.sha256(raw).hexdigest()
    get_storage_backend().save_bytes(storage_key, raw, file.content_type or "application/octet-stream")
    doc = DocumentFile(
        id=file_id,
        org_id=user.org_id,
        folder_id=folder_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(raw),
        storage_key=storage_key,
        sha256=digest,
        classification=classification,
        tags=json.loads(tags) if tags else [],
        retention_policy_id=retention_policy_id,
        created_by=user.id,
    )
    apply_training_mode(doc, request)
    db.add(doc)
    db.commit()
    version = DocumentVersion(
        org_id=user.org_id,
        file_id=doc.id,
        version_number=1,
        storage_key=storage_key,
        sha256=digest,
        size_bytes=len(raw),
        created_by=user.id,
    )
    apply_training_mode(version, request)
    db.add(version)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="upload",
        resource="documents_file",
        classification=doc.classification,
        after_state=model_snapshot(doc),
        event_type="documents.file.uploaded",
        event_payload={"file_id": doc.id},
    )
    return _serialize_file(doc, _legal_hold_count(db, user.org_id, doc.id), None)


@router.get("/files/{file_id}")
def get_file_metadata(
    file_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    doc = (
        scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
        .filter(DocumentFile.id == file_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not _has_permission(db, user, "file", file_id, "view"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    policy = None
    if doc.retention_policy_id:
        policy = (
            scoped_query(db, RetentionPolicy, user.org_id, request.state.training_mode)
            .filter(RetentionPolicy.id == doc.retention_policy_id)
            .first()
        )
    return _serialize_file(doc, _legal_hold_count(db, user.org_id, doc.id), policy)


@router.get("/files/{file_id}/download")
def download_file(
    file_id: str,
    request: Request,
    expires: Optional[int] = None,
    signature: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    doc = (
        scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
        .filter(DocumentFile.id == file_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not _has_permission(db, user, "file", file_id, "view"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    if signature and expires:
        if not _verify_signature(file_id, user.org_id, expires, signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    content = get_storage_backend().read_bytes(doc.storage_key)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="download",
        resource="documents_file",
        classification=doc.classification,
        after_state={"file_id": doc.id, "filename": doc.filename},
        event_type="documents.file.downloaded",
        event_payload={"file_id": doc.id},
    )
    return StreamingResponse(
        io.BytesIO(content),
        media_type=doc.content_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'},
    )


@router.post("/files/{file_id}/finalize")
def finalize_file(
    file_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.billing)),
):
    doc = (
        scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
        .filter(DocumentFile.id == file_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    hold = get_active_hold(db, user.org_id, "document_file", doc.id)
    decision = _policy_decision(db, request, user, doc, "finalize", hold=hold)
    if decision["decision"] == "BLOCK":
        return JSONResponse(status_code=status.HTTP_423_LOCKED, content=decision)
    before = model_snapshot(doc)
    doc.status = "FINALIZED"
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="finalize",
        resource="documents_file",
        classification=doc.classification,
        before_state=before,
        after_state=model_snapshot(doc),
        event_type="documents.file.finalized",
        event_payload={"file_id": doc.id},
    )
    return {"file": doc, "decision": decision}


@router.post("/files/{file_id}/move")
def move_file(
    file_id: str,
    folder_id: Optional[str] = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.billing)),
):
    doc = (
        scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
        .filter(DocumentFile.id == file_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    hold = get_active_hold(db, user.org_id, "document_file", doc.id)
    decision = _policy_decision(db, request, user, doc, "move", hold=hold)
    if decision["decision"] == "BLOCK":
        return JSONResponse(status_code=status.HTTP_423_LOCKED, content=decision)
    before = model_snapshot(doc)
    doc.folder_id = folder_id
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="move",
        resource="documents_file",
        classification=doc.classification,
        before_state=before,
        after_state=model_snapshot(doc),
        event_type="documents.file.moved",
        event_payload={"file_id": doc.id, "folder_id": folder_id},
    )
    return {"file": doc, "decision": decision}


@router.post("/files/{file_id}/tag")
def tag_file(
    file_id: str,
    tags: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.billing)),
):
    doc = (
        scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
        .filter(DocumentFile.id == file_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    hold = get_active_hold(db, user.org_id, "document_file", doc.id)
    decision = _policy_decision(db, request, user, doc, "tag", hold=hold)
    if decision["decision"] == "BLOCK":
        return JSONResponse(status_code=status.HTTP_423_LOCKED, content=decision)
    before = model_snapshot(doc)
    doc.tags = json.loads(tags)
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="tag",
        resource="documents_file",
        classification=doc.classification,
        before_state=before,
        after_state=model_snapshot(doc),
        event_type="documents.file.tagged",
        event_payload={"file_id": doc.id},
    )
    return {"file": doc, "decision": decision}


@router.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    doc = (
        scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
        .filter(DocumentFile.id == file_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    policy = None
    if doc.retention_policy_id:
        policy = (
            scoped_query(db, RetentionPolicy, user.org_id, request.state.training_mode)
            .filter(RetentionPolicy.id == doc.retention_policy_id)
            .first()
        )
    hold = get_active_hold(db, user.org_id, "document_file", doc.id)
    decision = _policy_decision(db, request, user, doc, "delete", policy=policy, hold=hold)
    if decision["decision"] == "BLOCK":
        return JSONResponse(status_code=status.HTTP_423_LOCKED, content=decision)
    before = model_snapshot(doc)
    doc.status = "DELETED_PENDING"
    db.commit()
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="delete_request",
        resource="documents_file",
        classification=doc.classification,
        before_state=before,
        after_state=model_snapshot(doc),
        event_type="documents.file.deleted_requested",
        event_payload={"file_id": doc.id},
    )
    return {"status": "queued", "file_id": doc.id, "decision": decision}


@router.post("/exports/discovery", status_code=status.HTTP_201_CREATED)
def create_discovery_export(
    request: Request,
    export_type: str = Form("custom_search"),
    folder_id: Optional[str] = Form(None),
    classification: Optional[str] = Form(None),
    tag: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.medical_director)),
):
    query = scoped_query(db, DocumentFile, user.org_id, request.state.training_mode)
    if folder_id:
        query = query.filter(DocumentFile.folder_id == folder_id)
    if classification:
        query = query.filter(DocumentFile.classification == classification)
    files = query.order_by(DocumentFile.created_at.desc()).all()
    if tag:
        files = [doc for doc in files if tag in (doc.tags or [])]
    export = DiscoveryExport(
        org_id=user.org_id,
        export_type=export_type,
        filters={"folder_id": folder_id, "classification": classification, "tag": tag},
        status="running",
        requested_by=user.id,
    )
    apply_training_mode(export, request)
    db.add(export)
    db.commit()
    db.refresh(export)

    manifest = {
        "export_id": export.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "sha256": doc.sha256,
                "classification": doc.classification,
            }
            for doc in files
        ],
    }
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_handle:
        zip_handle.writestr("manifest.json", json.dumps(manifest, indent=2))
        for doc in files:
            content = get_storage_backend().read_bytes(doc.storage_key)
            zip_handle.writestr(f"files/{doc.id}_{doc.filename}", content)
    archive.seek(0)
    payload = archive.read()
    sha256 = hashlib.sha256(payload).hexdigest()
    storage_key = build_storage_key(user.org_id, f"exports/{export.id}.zip")
    get_storage_backend().save_bytes(storage_key, payload, "application/zip")

    export.status = "complete"
    export.storage_key = storage_key
    export.sha256 = sha256
    export.completed_at = datetime.now(timezone.utc)
    db.commit()

    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="export",
        resource="documents_export",
        classification="LEGAL_HOLD",
        after_state=model_snapshot(export),
        event_type="documents.export.completed",
        event_payload={"export_id": export.id},
    )
    return {"status": "complete", "export_id": export.id}


@router.get("/exports/history")
def export_history(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.medical_director)),
):
    return scoped_query(db, DiscoveryExport, user.org_id, request.state.training_mode).order_by(
        DiscoveryExport.created_at.desc()
    ).all()


@router.get("/exports/{export_id}/download")
def download_export(
    export_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder, UserRole.medical_director)),
):
    export = (
        scoped_query(db, DiscoveryExport, user.org_id, request.state.training_mode)
        .filter(DiscoveryExport.id == export_id)
        .first()
    )
    if not export or not export.storage_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    payload = get_storage_backend().read_bytes(export.storage_key)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="download",
        resource="documents_export",
        classification="LEGAL_HOLD",
        after_state={"export_id": export.id},
        event_type="documents.export.downloaded",
        event_payload={"export_id": export.id},
    )
    return StreamingResponse(
        io.BytesIO(payload),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="export_{export.id}.zip"'},
    )
