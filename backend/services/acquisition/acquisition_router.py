"""
System Acquisition (SA) Router for FedRAMP Compliance

API endpoints for all SA controls (SA-2 through SA-22)
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import require_roles, get_current_user
from models.user import User, UserRole
from services.acquisition import (
    ResourceAllocationService,
    SDLCService,
    AcquisitionProcessService,
    SystemDocumentationService,
    SecurityEngineeringService,
    ExternalServicesService,
    DeveloperCMService,
    DeveloperTestingService,
    SupplyChainService,
    DevelopmentStandardsService,
    DeveloperTrainingService,
    DeveloperArchitectureService,
    DeveloperScreeningService,
    UnsupportedComponentsService,
)
from utils.write_ops import audit_and_event, model_snapshot
from utils.logger import logger

# Import models for response types
from models.acquisition import (
    SecurityBudget,
    SDLCProject,
    AcquisitionContract,
    SystemDocumentation,
    SecurityDesignReview,
    ExternalService,
    SourceCodeRepository,
    SecurityTest,
    SupplyChainComponent,
    DevelopmentTool,
    SecureCodingStandard,
    DeveloperTraining,
    DeveloperArchitecture,
    DeveloperScreening,
    UnsupportedComponent,
)


router = APIRouter(
    prefix="/api/v1/acquisition",
    tags=["System Acquisition"],
)


# ============================================================================
# SA-2: Allocation of Resources
# ============================================================================

class SecurityBudgetCreate(BaseModel):
    budget_name: str
    budget_category: str
    fiscal_year: int
    allocated_amount: float
    budget_description: Optional[str] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None


@router.post("/sa2/budgets", status_code=status.HTTP_201_CREATED)
async def create_budget(
    request_data: SecurityBudgetCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create a security budget (SA-2)"""
    service = ResourceAllocationService(db)
    budget = service.create_budget(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="security_budget",
        classification="SECURITY",
        after_state=model_snapshot(budget),
        event_type="acquisition.sa2.budget.created",
        event_payload={"budget_id": budget.id},
    )
    
    return budget


@router.get("/sa2/budgets")
async def list_budgets(
    fiscal_year: Optional[int] = Query(None),
    budget_category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List security budgets (SA-2)"""
    service = ResourceAllocationService(db)
    budgets, total = service.list_budgets(
        fiscal_year=fiscal_year,
        budget_category=budget_category,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {"budgets": budgets, "total": total}


@router.get("/sa2/budgets/summary")
async def get_budget_summary(
    fiscal_year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get budget summary (SA-2)"""
    service = ResourceAllocationService(db)
    return service.get_budget_summary(fiscal_year=fiscal_year)


# ============================================================================
# SA-3: System Development Life Cycle
# ============================================================================

class SDLCProjectCreate(BaseModel):
    project_name: str
    system_name: str
    project_description: Optional[str] = None
    system_id: Optional[str] = None
    project_manager: Optional[str] = None


@router.post("/sa3/projects", status_code=status.HTTP_201_CREATED)
async def create_sdlc_project(
    request_data: SDLCProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create an SDLC project (SA-3)"""
    service = SDLCService(db)
    project = service.create_project(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="sdlc_project",
        classification="SECURITY",
        after_state=model_snapshot(project),
        event_type="acquisition.sa3.project.created",
        event_payload={"project_id": project.id},
    )
    
    return project


@router.get("/sa3/projects/{project_id}/status")
async def get_project_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get SDLC project status (SA-3)"""
    service = SDLCService(db)
    return service.get_project_status(project_id)


# ============================================================================
# SA-4: Acquisition Process
# ============================================================================

class AcquisitionContractCreate(BaseModel):
    contract_number: str
    contract_name: str
    vendor_name: str
    security_requirements: Optional[List[str]] = None


@router.post("/sa4/contracts", status_code=status.HTTP_201_CREATED)
async def create_contract(
    request_data: AcquisitionContractCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create an acquisition contract (SA-4)"""
    service = AcquisitionProcessService(db)
    contract = service.create_contract(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="acquisition_contract",
        classification="SECURITY",
        after_state=model_snapshot(contract),
        event_type="acquisition.sa4.contract.created",
        event_payload={"contract_id": contract.id},
    )
    
    return contract


@router.get("/sa4/contracts/{contract_id}/summary")
async def get_contract_summary(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get contract summary (SA-4)"""
    service = AcquisitionProcessService(db)
    return service.get_contract_summary(contract_id)


# ============================================================================
# SA-5: Information System Documentation
# ============================================================================

class SystemDocumentationCreate(BaseModel):
    document_name: str
    document_type: str
    system_name: str
    version: str = "1.0"


@router.post("/sa5/documentation", status_code=status.HTTP_201_CREATED)
async def create_documentation(
    request_data: SystemDocumentationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create system documentation (SA-5)"""
    service = SystemDocumentationService(db)
    doc = service.create_documentation(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="system_documentation",
        classification="SECURITY",
        after_state=model_snapshot(doc),
        event_type="acquisition.sa5.documentation.created",
        event_payload={"documentation_id": doc.id},
    )
    
    return doc


@router.get("/sa5/documentation/summary")
async def get_documentation_summary(
    system_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get documentation summary (SA-5)"""
    service = SystemDocumentationService(db)
    return service.get_documentation_summary(system_name=system_name)


# ============================================================================
# SA-8: Security Engineering Principles
# ============================================================================

class SecurityDesignReviewCreate(BaseModel):
    review_name: str
    system_name: str
    principles_applied: Optional[List[str]] = None


@router.post("/sa8/design-reviews", status_code=status.HTTP_201_CREATED)
async def create_design_review(
    request_data: SecurityDesignReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create a security design review (SA-8)"""
    service = SecurityEngineeringService(db)
    review = service.create_design_review(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="security_design_review",
        classification="SECURITY",
        after_state=model_snapshot(review),
        event_type="acquisition.sa8.design_review.created",
        event_payload={"review_id": review.id},
    )
    
    return review


@router.get("/sa8/reviews/{review_id}/summary")
async def get_review_summary(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get design review summary (SA-8)"""
    service = SecurityEngineeringService(db)
    return service.get_review_summary(review_id)


# ============================================================================
# SA-9: External Information System Services
# ============================================================================

class ExternalServiceCreate(BaseModel):
    service_name: str
    service_type: str
    provider_name: str
    data_types_processed: Optional[List[str]] = None


@router.post("/sa9/services", status_code=status.HTTP_201_CREATED)
async def create_external_service(
    request_data: ExternalServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create an external service (SA-9)"""
    service = ExternalServicesService(db)
    external_service = service.create_external_service(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="external_service",
        classification="SECURITY",
        after_state=model_snapshot(external_service),
        event_type="acquisition.sa9.service.created",
        event_payload={"service_id": external_service.id},
    )
    
    return external_service


@router.get("/sa9/services/{service_id}/summary")
async def get_service_summary(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get external service summary (SA-9)"""
    service = ExternalServicesService(db)
    return service.get_service_summary(service_id)


# ============================================================================
# SA-10: Developer Configuration Management
# ============================================================================

class SourceCodeRepositoryCreate(BaseModel):
    repository_name: str
    repository_url: str
    system_name: str
    repository_type: str = "git"


@router.post("/sa10/repositories", status_code=status.HTTP_201_CREATED)
async def create_repository(
    request_data: SourceCodeRepositoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create a source code repository (SA-10)"""
    service = DeveloperCMService(db)
    repo = service.create_repository(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="source_code_repository",
        classification="SECURITY",
        after_state=model_snapshot(repo),
        event_type="acquisition.sa10.repository.created",
        event_payload={"repository_id": repo.id},
    )
    
    return repo


@router.get("/sa10/repositories/{repository_id}/summary")
async def get_repository_summary(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get repository summary (SA-10)"""
    service = DeveloperCMService(db)
    return service.get_repository_summary(repository_id)


# ============================================================================
# SA-11: Developer Security Testing
# ============================================================================

class SecurityTestCreate(BaseModel):
    test_name: str
    test_type: str
    system_name: str
    build_id: Optional[int] = None


@router.post("/sa11/tests", status_code=status.HTTP_201_CREATED)
async def create_security_test(
    request_data: SecurityTestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create a security test (SA-11)"""
    service = DeveloperTestingService(db)
    test = service.create_security_test(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="security_test",
        classification="SECURITY",
        after_state=model_snapshot(test),
        event_type="acquisition.sa11.test.created",
        event_payload={"test_id": test.id},
    )
    
    return test


@router.get("/sa11/tests/{test_id}/summary")
async def get_test_summary(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get security test summary (SA-11)"""
    service = DeveloperTestingService(db)
    return service.get_test_summary(test_id)


# ============================================================================
# SA-12: Supply Chain Risk Management
# ============================================================================

class SupplyChainComponentCreate(BaseModel):
    component_name: str
    component_type: str
    supplier_name: str
    system_name: str


@router.post("/sa12/components", status_code=status.HTTP_201_CREATED)
async def create_component(
    request_data: SupplyChainComponentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create a supply chain component (SA-12)"""
    service = SupplyChainService(db)
    component = service.create_component(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="supply_chain_component",
        classification="SECURITY",
        after_state=model_snapshot(component),
        event_type="acquisition.sa12.component.created",
        event_payload={"component_id": component.id},
    )
    
    return component


@router.get("/sa12/summary")
async def get_supply_chain_summary(
    system_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get supply chain summary (SA-12)"""
    service = SupplyChainService(db)
    return service.get_supply_chain_summary(system_name=system_name)


# ============================================================================
# SA-15: Development Process, Standards, and Tools
# ============================================================================

class DevelopmentToolCreate(BaseModel):
    tool_name: str
    tool_type: str
    tool_vendor: Optional[str] = None


@router.post("/sa15/tools", status_code=status.HTTP_201_CREATED)
async def create_tool(
    request_data: DevelopmentToolCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create a development tool (SA-15)"""
    service = DevelopmentStandardsService(db)
    tool = service.create_tool(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="development_tool",
        classification="SECURITY",
        after_state=model_snapshot(tool),
        event_type="acquisition.sa15.tool.created",
        event_payload={"tool_id": tool.id},
    )
    
    return tool


@router.get("/sa15/compliance/summary")
async def get_compliance_summary(
    system_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get compliance summary (SA-15)"""
    service = DevelopmentStandardsService(db)
    return service.get_compliance_summary(system_name=system_name)


# ============================================================================
# SA-16: Developer-Provided Training
# ============================================================================

class DeveloperTrainingCreate(BaseModel):
    training_name: str
    training_type: str
    mandatory: bool = True


@router.post("/sa16/training", status_code=status.HTTP_201_CREATED)
async def create_training(
    request_data: DeveloperTrainingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create developer training (SA-16)"""
    service = DeveloperTrainingService(db)
    training = service.create_training(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="developer_training",
        classification="SECURITY",
        after_state=model_snapshot(training),
        event_type="acquisition.sa16.training.created",
        event_payload={"training_id": training.id},
    )
    
    return training


@router.get("/sa16/training/summary")
async def get_training_summary(
    developer_email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get training summary (SA-16)"""
    service = DeveloperTrainingService(db)
    return service.get_training_summary(developer_email=developer_email)


# ============================================================================
# SA-17: Developer Security Architecture
# ============================================================================

class DeveloperArchitectureCreate(BaseModel):
    architecture_name: str
    system_name: str
    security_patterns_used: Optional[List[str]] = None


@router.post("/sa17/architectures", status_code=status.HTTP_201_CREATED)
async def create_architecture(
    request_data: DeveloperArchitectureCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create developer architecture (SA-17)"""
    service = DeveloperArchitectureService(db)
    architecture = service.create_architecture(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="developer_architecture",
        classification="SECURITY",
        after_state=model_snapshot(architecture),
        event_type="acquisition.sa17.architecture.created",
        event_payload={"architecture_id": architecture.id},
    )
    
    return architecture


@router.get("/sa17/architectures/{architecture_id}/summary")
async def get_architecture_summary(
    architecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get architecture summary (SA-17)"""
    service = DeveloperArchitectureService(db)
    return service.get_architecture_summary(architecture_id)


# ============================================================================
# SA-21: Developer Screening
# ============================================================================

class DeveloperScreeningCreate(BaseModel):
    developer_name: str
    screening_type: str
    developer_email: Optional[str] = None


@router.post("/sa21/screenings", status_code=status.HTTP_201_CREATED)
async def create_screening(
    request_data: DeveloperScreeningCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create developer screening (SA-21)"""
    service = DeveloperScreeningService(db)
    screening = service.create_screening(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="developer_screening",
        classification="SECURITY",
        after_state=model_snapshot(screening),
        event_type="acquisition.sa21.screening.created",
        event_payload={"screening_id": screening.id},
    )
    
    return screening


@router.get("/sa21/screenings/summary")
async def get_screening_summary(
    developer_email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get screening summary (SA-21)"""
    service = DeveloperScreeningService(db)
    return service.get_screening_summary(developer_email=developer_email)


# ============================================================================
# SA-22: Unsupported System Components
# ============================================================================

class UnsupportedComponentCreate(BaseModel):
    component_name: str
    component_type: str
    system_name: str
    eol_date: Optional[datetime] = None


@router.post("/sa22/components", status_code=status.HTTP_201_CREATED)
async def create_unsupported_component(
    request_data: UnsupportedComponentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SECURITY_ADMIN, UserRole.ADMIN)),
):
    """Create unsupported component record (SA-22)"""
    service = UnsupportedComponentsService(db)
    component = service.create_component(**request_data.dict())
    
    audit_and_event(
        db=db,
        request=request,
        user=current_user,
        action="create",
        resource="unsupported_component",
        classification="SECURITY",
        after_state=model_snapshot(component),
        event_type="acquisition.sa22.component.created",
        event_payload={"component_id": component.id},
    )
    
    return component


@router.get("/sa22/components/summary")
async def get_unsupported_components_summary(
    system_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get unsupported components summary (SA-22)"""
    service = UnsupportedComponentsService(db)
    return service.get_component_summary(system_name=system_name)


# ============================================================================
# Integration with Vulnerability and Risk Systems
# ============================================================================

@router.get("/integration/vulnerabilities")
async def get_vulnerability_integration(
    system_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability integration data for SA controls"""
    # This would integrate with the existing vulnerability system
    # For now, return a placeholder structure
    return {
        "message": "Vulnerability integration endpoint",
        "system_name": system_name,
        "note": "This endpoint integrates with backend/models/vulnerability.py",
    }


@router.get("/integration/risk-assessments")
async def get_risk_assessment_integration(
    system_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get risk assessment integration data for SA controls"""
    # This would integrate with the existing risk assessment system
    # For now, return a placeholder structure
    return {
        "message": "Risk assessment integration endpoint",
        "system_name": system_name,
        "note": "This endpoint integrates with backend/models/risk_assessment.py",
    }
