"""
Founder Terminology Builder - NEMSIS-constrained ICD-10, SNOMED, RXNorm.

Founders can add/remove/adjust codes for ePCR and billing; all entries
reference NEMSIS elements so exports stay CMS/NEMSIS compliant.
AI suggest uses Ollama to suggest codes from free text (chief complaint, etc.).
"""
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles
from models.terminology_builder import TerminologyEntry
from models.user import User, UserRole
from utils.tenancy import scoped_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/founder/terminology", tags=["Founder Terminology Builder"])


class TerminologySuggestRequest(BaseModel):
    query: str  # e.g. "chest pain", "IV access"
    code_set: str = "icd10"  # icd10, snomed, rxnorm


class TerminologySuggestResponse(BaseModel):
    suggestions: List[Dict[str, Any]]  # [{ "code", "description", "nemsis_element_ref" }]
    explanation: Optional[str] = None
    ai_available: bool = False


class TerminologyEntryCreate(BaseModel):
    code_set: str  # icd10, snomed, rxnorm
    use_case: str  # diagnosis, intervention, medication
    code: str
    description: str
    alternate_text: Optional[str] = None
    nemsis_element_ref: Optional[str] = None
    nemsis_value_set: Optional[str] = None
    active: bool = True
    sort_order: int = 0


class TerminologyEntryUpdate(BaseModel):
    description: Optional[str] = None
    alternate_text: Optional[str] = None
    nemsis_element_ref: Optional[str] = None
    nemsis_value_set: Optional[str] = None
    active: Optional[bool] = None
    sort_order: Optional[int] = None


class TerminologyEntryOut(BaseModel):
    id: int
    code_set: str
    use_case: str
    code: str
    description: str
    alternate_text: Optional[str]
    nemsis_element_ref: Optional[str]
    nemsis_value_set: Optional[str]
    active: bool
    sort_order: int

    class Config:
        from_attributes = True


@router.get("", response_model=List[TerminologyEntryOut])
def list_terminology(
    code_set: Optional[str] = Query(None, description="icd10, snomed, rxnorm"),
    use_case: Optional[str] = Query(None, description="diagnosis, intervention, medication"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """List terminology entries; filter by code_set (ICD-10, SNOMED, RXNorm) and use_case."""
    q = scoped_query(db, TerminologyEntry, user.org_id, None)
    if code_set:
        q = q.filter(TerminologyEntry.code_set == code_set)
    if use_case:
        q = q.filter(TerminologyEntry.use_case == use_case)
    if active_only:
        q = q.filter(TerminologyEntry.active == True)
    rows = q.order_by(TerminologyEntry.sort_order, TerminologyEntry.code).all()
    return [TerminologyEntryOut.model_validate(r) for r in rows]


def do_suggest_terminology(query: str, code_set: str = "icd10") -> TerminologySuggestResponse:
    """Shared AI-suggest logic for ICD-10, SNOMED, RXNorm. Used by founder and ePCR routes."""
    suggestions: List[Dict[str, Any]] = []
    explanation: Optional[str] = None
    ai_available = False
    try:
        from services.billing.assist_service import OllamaClient
        from core.config import settings
        client = OllamaClient()
        if getattr(settings, "OLLAMA_ENABLED", False) and client.base_url:
            ai_available = True
            code_set_label = {"icd10": "ICD-10", "snomed": "SNOMED", "rxnorm": "RXNorm"}.get(code_set, code_set)
            prompt = (
                f"You are a medical coding assistant for EMS ePCR. Suggest up to 5 {code_set_label} codes "
                f"that are NEMSIS-appropriate for: \"{query}\". "
                f"Reply with one code per line in format: CODE | Description (e.g. R07.9 | Chest pain, unspecified). "
                f"No other text."
            )
            result = client.generate(prompt, model=getattr(settings, "OLLAMA_IVR_MODEL", "llama3.2") or "llama3.2", temperature=0.2)
            if result.get("status") == "ok" and result.get("response"):
                text = result["response"].strip()
                explanation = f"AI suggested codes for \"{query}\"."
                for line in text.split("\n")[:10]:
                    line = line.strip()
                    if "|" in line:
                        code, desc = line.split("|", 1)
                        code, desc = code.strip(), desc.strip()
                        if code and desc:
                            suggestions.append({"code": code, "description": desc, "nemsis_element_ref": None})
                    elif re.match(r"^[A-Z][0-9]{2}(\.[0-9]+)?", line) or re.match(r"^\d+", line):
                        parts = line.split(None, 1)
                        if len(parts) >= 2:
                            suggestions.append({"code": parts[0], "description": parts[1], "nemsis_element_ref": None})
            else:
                explanation = "Ollama did not return suggestions. Add codes manually or check Ollama is running."
        else:
            explanation = "AI (Ollama) is not enabled. Add codes manually or enable OLLAMA_ENABLED and OLLAMA_SERVER_URL."
    except Exception as e:
        logger.warning("Terminology suggest failed: %s", e)
        explanation = f"AI suggest unavailable: {e}. Add codes manually."
    return TerminologySuggestResponse(suggestions=suggestions, explanation=explanation, ai_available=ai_available)


@router.post("/suggest", response_model=TerminologySuggestResponse)
def suggest_terminology(
    payload: TerminologySuggestRequest,
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """AI-suggest ICD-10, SNOMED, or RXNorm codes from free text (e.g. chief complaint). Uses Ollama when enabled."""
    return do_suggest_terminology(payload.query, payload.code_set)


@router.post("", response_model=TerminologyEntryOut, status_code=201)
def create_terminology_entry(
    payload: TerminologyEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """Add a new ICD-10, SNOMED, or RXNorm entry (NEMSIS-constrained)."""
    if payload.code_set not in ("icd10", "snomed", "rxnorm"):
        raise HTTPException(status_code=400, detail="code_set must be icd10, snomed, or rxnorm")
    # ICD-10 use_case: diagnosis (chief complaint), impression (clinical impression), medication_history (condition for med)
    if payload.code_set == "icd10" and payload.use_case not in ("diagnosis", "impression", "medication_history"):
        raise HTTPException(status_code=400, detail="For icd10, use_case must be diagnosis, impression, or medication_history")
    entry = TerminologyEntry(
        org_id=user.org_id,
        code_set=payload.code_set,
        use_case=payload.use_case,
        code=payload.code.strip(),
        description=payload.description.strip(),
        alternate_text=payload.alternate_text.strip() if payload.alternate_text else None,
        nemsis_element_ref=payload.nemsis_element_ref or None,
        nemsis_value_set=payload.nemsis_value_set or None,
        active=payload.active,
        sort_order=payload.sort_order,
        created_by=user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return TerminologyEntryOut.model_validate(entry)


@router.patch("/{entry_id}", response_model=TerminologyEntryOut)
def update_terminology_entry(
  entry_id: int,
  payload: TerminologyEntryUpdate,
  db: Session = Depends(get_db),
  user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """Update wording or NEMSIS ref for an entry."""
    entry = (
        scoped_query(db, TerminologyEntry, user.org_id, None)
        .filter(TerminologyEntry.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Terminology entry not found")
    if payload.description is not None:
        entry.description = payload.description.strip()
    if payload.alternate_text is not None:
        entry.alternate_text = payload.alternate_text.strip() or None
    if payload.nemsis_element_ref is not None:
        entry.nemsis_element_ref = payload.nemsis_element_ref or None
    if payload.nemsis_value_set is not None:
        entry.nemsis_value_set = payload.nemsis_value_set or None
    if payload.active is not None:
        entry.active = payload.active
    if payload.sort_order is not None:
        entry.sort_order = payload.sort_order
    db.commit()
    db.refresh(entry)
    return TerminologyEntryOut.model_validate(entry)


@router.delete("/{entry_id}", status_code=204)
def delete_terminology_entry(
  entry_id: int,
  db: Session = Depends(get_db),
  user: User = Depends(require_roles(UserRole.founder, UserRole.admin)),
):
    """Remove a terminology entry (or deactivate: use PATCH active=false)."""
    entry = (
        scoped_query(db, TerminologyEntry, user.org_id, None)
        .filter(TerminologyEntry.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Terminology entry not found")
    db.delete(entry)
    db.commit()
    return None
