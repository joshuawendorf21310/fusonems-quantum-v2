import re
import uuid
from datetime import datetime
from typing import Optional


def sanitize_filename(filename: str) -> str:
    safe = re.sub(r'[^\w\s\-\.]', '', filename)
    safe = re.sub(r'\.\.+', '.', safe)
    safe = safe.replace('/', '_').replace('\\', '_')
    return safe.strip()


def build_storage_path(
    org_id: str,
    system: str,
    object_type: str,
    object_id: str,
    filename: str,
    add_timestamp: bool = False
) -> str:
    safe_filename = sanitize_filename(filename)
    
    if add_timestamp:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        name_parts = safe_filename.rsplit('.', 1)
        if len(name_parts) == 2:
            safe_filename = f"{timestamp}_{name_parts[0]}.{name_parts[1]}"
        else:
            safe_filename = f"{timestamp}_{safe_filename}"
    
    return f"{org_id}/{system}/{object_type}/{object_id}/{safe_filename}"


def validate_system(system: str) -> bool:
    valid_systems = {"workspace", "accounting", "communications", "app-builder", "founder"}
    return system in valid_systems


def validate_object_type(system: str, object_type: str) -> bool:
    valid_types = {
        "workspace": {"doc", "sheet", "slide", "pdf"},
        "accounting": {"receipt", "invoice", "export"},
        "communications": {"email-attachment", "message-attachment"},
        "app-builder": {"source", "build"},
        "founder": {"file", "content"},
    }
    return object_type in valid_types.get(system, set())
