"""
Planning (PL) Router for FedRAMP Compliance

Endpoints for:
- PL-2: System Security Plan (SSP)
- PL-4: Rules of Behavior
- PL-7: Security Concept of Operations (CONOPS)
- PL-8: Information Security Architecture
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from core.database import get_db
from core.security import require_roles
from models.user import User, UserRole
from services.planning.ssp_generator_service import SSPGeneratorService
from services.planning.rules_of_behavior_service import RulesOfBehaviorService
from services.planning.conops_generator_service import CONOPSGeneratorService
from services.planning.security_architecture_service import SecurityArchitectureService


router = APIRouter(prefix="/api/compliance/planning", tags=["Planning (PL)"])


# ============================================================================
# PL-2: System Security Plan (SSP)
# ============================================================================

class CreateSSPRequest(BaseModel):
    ssp_name: str
    system_name: str
    system_id: Optional[str] = None
    system_description: Optional[str] = None
    system_owner: Optional[str] = None


class AddControlSectionRequest(BaseModel):
    control_family: str
    control_id: str
    control_title: str
    implementation_description: str
    implementation_status: str = "planned"
    implementation_narrative: Optional[str] = None
    responsible_role: Optional[str] = None
    responsible_party: Optional[str] = None


@router.post("/ssp/create")
def create_ssp(
    request: CreateSSPRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Create a new System Security Plan"""
    service = SSPGeneratorService(db, user.org_id, user.id)
    ssp = service.create_ssp(**request.dict())
    return {"ssp_id": str(ssp.id), "message": "SSP created successfully"}


@router.post("/ssp/{ssp_id}/add-control")
def add_control_section(
    ssp_id: str,
    request: AddControlSectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Add a control section to SSP"""
    service = SSPGeneratorService(db, user.org_id, user.id)
    section = service.add_control_section(ssp_id, **request.dict())
    return {"section_id": str(section.id), "message": "Control section added"}


@router.get("/ssp/{ssp_id}/generate-pdf")
def generate_ssp_pdf(
    ssp_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Generate SSP PDF document"""
    service = SSPGeneratorService(db, user.org_id, user.id)
    pdf_bytes = service.generate_ssp_document(ssp_id)
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/ssp/{ssp_id}/evidence")
def collect_ssp_evidence(
    ssp_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Collect evidence for SSP"""
    service = SSPGeneratorService(db, user.org_id, user.id)
    evidence = service.collect_evidence(ssp_id)
    return evidence


@router.post("/ssp/{ssp_id}/approve")
def approve_ssp(
    ssp_id: str,
    approval_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder))
):
    """Approve SSP"""
    service = SSPGeneratorService(db, user.org_id, user.id)
    ssp = service.approve_ssp(ssp_id, approval_notes)
    return {"message": "SSP approved", "ssp_id": str(ssp.id)}


# ============================================================================
# PL-4: Rules of Behavior
# ============================================================================

class CreateRulesRequest(BaseModel):
    title: str
    rules_content: str
    version: str = "1.0"
    rules_sections: Optional[dict] = None


@router.post("/rules/create")
def create_rules(
    request: CreateRulesRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Create Rules of Behavior"""
    service = RulesOfBehaviorService(db, user.org_id, user.id)
    rules = service.create_rules(**request.dict())
    return {"rules_id": str(rules.id), "message": "Rules created successfully"}


@router.get("/rules/{rules_id}/generate-pdf")
def generate_rules_pdf(
    rules_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Generate Rules of Behavior PDF"""
    service = RulesOfBehaviorService(db, user.org_id, user.id)
    pdf_bytes = service.generate_rules_document(rules_id)
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/rules/{rules_id}/acknowledge")
def acknowledge_rules(
    rules_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles())
):
    """Acknowledge Rules of Behavior"""
    service = RulesOfBehaviorService(db, user.org_id, user.id)
    ack = service.acknowledge_rules(rules_id, user.id, ip_address, user_agent)
    return {"message": "Rules acknowledged", "acknowledgment_id": str(ack.id)}


@router.get("/rules/{rules_id}/acknowledgment-status")
def get_acknowledgment_status(
    rules_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Get acknowledgment status for Rules of Behavior"""
    service = RulesOfBehaviorService(db, user.org_id, user.id)
    status = service.get_acknowledgment_status(rules_id)
    return status


@router.post("/rules/{rules_id}/activate")
def activate_rules(
    rules_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder))
):
    """Activate Rules of Behavior"""
    service = RulesOfBehaviorService(db, user.org_id, user.id)
    rules = service.activate_rules(rules_id)
    return {"message": "Rules activated", "rules_id": str(rules.id)}


# ============================================================================
# PL-7: Security CONOPS
# ============================================================================

class CreateCONOPSRequest(BaseModel):
    title: str
    system_name: str
    version: str = "1.0"
    system_overview: Optional[str] = None
    operational_environment: Optional[str] = None
    operational_procedures: Optional[str] = None
    security_procedures: Optional[str] = None
    system_architecture: Optional[str] = None


@router.post("/conops/create")
def create_conops(
    request: CreateCONOPSRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Create Security CONOPS"""
    service = CONOPSGeneratorService(db, user.org_id, user.id)
    conops = service.create_conops(**request.dict())
    return {"conops_id": str(conops.id), "message": "CONOPS created successfully"}


@router.get("/conops/{conops_id}/generate-pdf")
def generate_conops_pdf(
    conops_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Generate CONOPS PDF"""
    service = CONOPSGeneratorService(db, user.org_id, user.id)
    pdf_bytes = service.generate_conops_document(conops_id)
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/conops/{conops_id}/approve")
def approve_conops(
    conops_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder))
):
    """Approve CONOPS"""
    service = CONOPSGeneratorService(db, user.org_id, user.id)
    conops = service.approve_conops(conops_id)
    return {"message": "CONOPS approved", "conops_id": str(conops.id)}


# ============================================================================
# PL-8: Information Security Architecture
# ============================================================================

class CreateArchitectureRequest(BaseModel):
    title: str
    system_name: str
    version: str = "1.0"
    components: Optional[List[dict]] = None
    component_relationships: Optional[dict] = None
    security_boundaries: Optional[str] = None
    security_controls: Optional[dict] = None


@router.post("/architecture/create")
def create_architecture(
    request: CreateArchitectureRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Create Information Security Architecture"""
    service = SecurityArchitectureService(db, user.org_id, user.id)
    architecture = service.create_architecture(**request.dict())
    return {"architecture_id": str(architecture.id), "message": "Architecture created successfully"}


@router.get("/architecture/{architecture_id}/generate-pdf")
def generate_architecture_pdf(
    architecture_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder, UserRole.admin))
):
    """Generate Security Architecture PDF"""
    service = SecurityArchitectureService(db, user.org_id, user.id)
    pdf_bytes = service.generate_architecture_document(architecture_id)
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/architecture/{architecture_id}/approve")
def approve_architecture(
    architecture_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.founder))
):
    """Approve Security Architecture"""
    service = SecurityArchitectureService(db, user.org_id, user.id)
    architecture = service.approve_architecture(architecture_id)
    return {"message": "Architecture approved", "architecture_id": str(architecture.id)}
