"""
Founder Documents (Drive) - files and folders in DigitalOcean Spaces.
Frontend Office 365-style docs call these endpoints; storage is Spaces (S3-compatible).
"""
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.founder_documents import FounderDocumentFile, FounderDocumentFolder
from models.user import User, UserRole
from services.storage.storage_service import get_storage_service, UploadContext
from services.storage.path_utils import build_storage_path

router = APIRouter(prefix="/api/founder/documents", tags=["founder-documents"])


class FolderOut(BaseModel):
    id: int
    name: str
    parentId: Optional[int] = None

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    name: str
    type: str
    url: str
    tags: List[str]
    folderId: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True


def _signed_url(storage_key: str, expires: int = 3600) -> str:
    try:
        return get_storage_service().generate_signed_url(file_path=storage_key, expires_in=expires)
    except Exception:
        return ""


@router.get("/folders", response_model=List[FolderOut])
def list_folders(
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    # Add pagination to prevent performance issues with large folder datasets
    rows = db.query(FounderDocumentFolder).filter(FounderDocumentFolder.org_id == org_id).order_by(FounderDocumentFolder.name).offset(offset).limit(limit).all()
    return [FolderOut(id=r.id, name=r.name, parentId=r.parent_id) for r in rows]


@router.post("/folders", response_model=FolderOut)
def create_folder(
    name: str = Form(...),
    parent_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    folder = FounderDocumentFolder(org_id=org_id, name=name.strip(), parent_id=parent_id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return FolderOut(id=folder.id, name=folder.name, parentId=folder.parent_id)


@router.get("/records", response_model=List[DocumentOut])
def list_documents(
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    # Add pagination to prevent performance issues with large document datasets
    rows = db.query(FounderDocumentFile).filter(FounderDocumentFile.org_id == org_id).order_by(FounderDocumentFile.created_at.desc()).offset(offset).limit(limit).all()
    out = []
    for r in rows:
        url = _signed_url(r.storage_key)
        out.append(
            DocumentOut(
                id=r.id,
                name=r.name,
                type=r.mime_type or "application/octet-stream",
                url=url,
                tags=r.tags or [],
                folderId=r.folder_id,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
        )
    return out


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    data = await file.read()
    filename = file.filename or "unnamed"
    object_id = str(uuid.uuid4())
    storage = get_storage_service()
    ctx = UploadContext(org_id=str(org_id), system="founder", object_type="file", object_id=object_id, user_id=user.id, role=getattr(user, "role", None))
    meta = storage.upload_file(file_data=data, filename=filename, context=ctx, mime_type=file.content_type or "application/octet-stream", add_timestamp=False)
    rec = FounderDocumentFile(
        org_id=org_id,
        name=filename,
        storage_key=meta.file_path,
        mime_type=meta.mime_type,
        size=meta.size,
        folder_id=folder_id,
        tags=[],
        created_by=user.id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    url = _signed_url(rec.storage_key)
    return DocumentOut(
        id=rec.id,
        name=rec.name,
        type=rec.mime_type or "application/octet-stream",
        url=url,
        tags=rec.tags or [],
        folderId=rec.folder_id,
        created_at=rec.created_at.isoformat() if rec.created_at else "",
    )


@router.post("/files/{file_id}/move")
def move_file(
    file_id: int,
    folder_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    rec = db.query(FounderDocumentFile).filter(FounderDocumentFile.id == file_id, FounderDocumentFile.org_id == org_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    rec.folder_id = folder_id
    db.commit()
    return {"status": "ok"}


@router.post("/files/{file_id}/tag")
def tag_file(
    file_id: int,
    tags: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    rec = db.query(FounderDocumentFile).filter(FounderDocumentFile.id == file_id, FounderDocumentFile.org_id == org_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        rec.tags = json.loads(tags) if isinstance(tags, str) else (tags if isinstance(tags, list) else [])
    except Exception:
        rec.tags = []
    db.commit()
    return {"status": "ok"}


@router.put("/files/{file_id}/content")
async def save_file_content(
    file_id: int,
    body: dict = Body(..., embed=False),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    """Save editable document content to DigitalOcean Spaces. Content is stored at content_key."""
    org_id = user.org_id
    rec = db.query(FounderDocumentFile).filter(FounderDocumentFile.id == file_id, FounderDocumentFile.org_id == org_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    content = (body.get("content") or "").encode("utf-8")
    storage = get_storage_service()
    ctx = UploadContext(org_id=str(org_id), system="founder", object_type="content", object_id=str(rec.id), user_id=user.id)
    meta = storage.upload_file(file_data=content, filename="content.html", context=ctx, mime_type="text/html", add_timestamp=False)
    rec.content_key = meta.file_path
    db.commit()
    return {"status": "ok", "content_key": meta.file_path}


@router.get("/files/{file_id}/content")
def get_file_content(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    rec = db.query(FounderDocumentFile).filter(FounderDocumentFile.id == file_id, FounderDocumentFile.org_id == org_id).first()
    if not rec or not rec.content_key:
        raise HTTPException(status_code=404, detail="File or content not found")
    try:
        data = get_storage_service().download_file(rec.content_key)
        return {"content": data.decode("utf-8", errors="replace")}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to load content: {e}")


@router.get("/files/{file_id}/url")
def get_file_url(
    file_id: int,
    expires: int = 3600,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.founder)),
):
    org_id = user.org_id
    rec = db.query(FounderDocumentFile).filter(FounderDocumentFile.id == file_id, FounderDocumentFile.org_id == org_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    url = _signed_url(rec.storage_key, expires=expires)
    return {"url": url}
