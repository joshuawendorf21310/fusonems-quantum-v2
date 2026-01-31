from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
from core.database import get_db
from core.security import require_roles
from models.user import User, UserRole
import os
import re

router = APIRouter(prefix="/api/admin/protocols", tags=["Protocols"])

UPLOAD_DIR = os.environ.get("PROTOCOL_UPLOAD_DIR", "./uploads/protocols")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks
    Removes any path separators and potentially dangerous characters
    """
    # Get just the basename (removes any directory path)
    filename = os.path.basename(filename)
    # Remove any remaining path traversal attempts
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    # Allow only alphanumeric, dots, dashes, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Ensure filename is not empty
    if not filename or filename == '.':
        filename = 'unnamed_file'
    return filename

@router.post("/import")
def import_protocol(
    protocol: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    # Sanitize the filename to prevent path traversal
    safe_filename = sanitize_filename(protocol.filename or "protocol")
    filename = f"{user.org_id}_{safe_filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Additional security: ensure the resolved path is still within UPLOAD_DIR
    upload_dir_abs = Path(UPLOAD_DIR).resolve()
    file_path_abs = Path(file_path).resolve()
    if not str(file_path_abs).startswith(str(upload_dir_abs)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    with open(file_path, "wb") as f:
        f.write(protocol.file.read())
    # TODO: Parse/validate protocol, store metadata, trigger review workflow
    return JSONResponse({"status": "success", "filename": filename})
