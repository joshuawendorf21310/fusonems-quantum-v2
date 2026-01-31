"""
SA-3: System Development Life Cycle Service

FedRAMP SA-3 compliance service for:
- SDLC phase tracking
- Security gate enforcement
- Phase approvals
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    SDLCProject,
    SDLCPhase,
    SecurityGate,
    SDLCPhase as SDLCPhaseEnum,
    PhaseStatus,
    SecurityGateStatus,
)


class SDLCService:
    """Service for SA-3: System Development Life Cycle"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_project(
        self,
        project_name: str,
        system_name: str,
        project_description: Optional[str] = None,
        system_id: Optional[str] = None,
        project_manager: Optional[str] = None,
        start_date: Optional[datetime] = None,
        target_completion_date: Optional[datetime] = None,
    ) -> SDLCProject:
        """Create a new SDLC project"""
        project = SDLCProject(
            project_name=project_name,
            project_description=project_description,
            system_name=system_name,
            system_id=system_id,
            project_manager=project_manager,
            start_date=start_date,
            target_completion_date=target_completion_date,
            current_phase=SDLCPhaseEnum.INITIATION.value,
            project_status=PhaseStatus.NOT_STARTED.value,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def create_phase(
        self,
        sdlc_project_id: int,
        phase_name: SDLCPhaseEnum,
        phase_order: int,
        phase_description: Optional[str] = None,
        planned_start_date: Optional[datetime] = None,
        planned_end_date: Optional[datetime] = None,
        deliverables: Optional[List[str]] = None,
    ) -> SDLCPhase:
        """Create an SDLC phase"""
        phase = SDLCPhase(
            sdlc_project_id=sdlc_project_id,
            phase_name=phase_name.value,
            phase_description=phase_description,
            phase_order=phase_order,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            deliverables=deliverables,
            status=PhaseStatus.NOT_STARTED.value,
            completion_percentage=0.0,
        )
        self.db.add(phase)
        self.db.commit()
        self.db.refresh(phase)
        return phase
    
    def update_phase_status(
        self,
        phase_id: int,
        status: Optional[PhaseStatus] = None,
        completion_percentage: Optional[float] = None,
        actual_start_date: Optional[datetime] = None,
        actual_end_date: Optional[datetime] = None,
        deliverables_completed: Optional[List[str]] = None,
    ) -> SDLCPhase:
        """Update phase status"""
        phase = self.db.query(SDLCPhase).filter(SDLCPhase.id == phase_id).first()
        if not phase:
            raise ValueError(f"Phase {phase_id} not found")
        
        if status:
            phase.status = status.value
            if status == PhaseStatus.IN_PROGRESS and not phase.actual_start_date:
                phase.actual_start_date = datetime.utcnow()
            elif status == PhaseStatus.COMPLETED and not phase.actual_end_date:
                phase.actual_end_date = datetime.utcnow()
                phase.completion_percentage = 100.0
        
        if completion_percentage is not None:
            phase.completion_percentage = completion_percentage
        
        if actual_start_date:
            phase.actual_start_date = actual_start_date
        
        if actual_end_date:
            phase.actual_end_date = actual_end_date
        
        if deliverables_completed is not None:
            phase.deliverables_completed = deliverables_completed
        
        self.db.commit()
        self.db.refresh(phase)
        
        # Update project current phase if needed
        self._update_project_phase(phase.sdlc_project_id)
        
        return phase
    
    def approve_phase(
        self,
        phase_id: int,
        approved_by: str,
        approval_notes: Optional[str] = None,
    ) -> SDLCPhase:
        """Approve an SDLC phase"""
        phase = self.db.query(SDLCPhase).filter(SDLCPhase.id == phase_id).first()
        if not phase:
            raise ValueError(f"Phase {phase_id} not found")
        
        phase.approved = True
        phase.approved_by = approved_by
        phase.approval_date = datetime.utcnow()
        phase.approval_notes = approval_notes
        
        self.db.commit()
        self.db.refresh(phase)
        return phase
    
    def create_security_gate(
        self,
        sdlc_project_id: int,
        gate_name: str,
        gate_type: str,
        phase_id: Optional[int] = None,
        gate_description: Optional[str] = None,
        requirements: Optional[List[str]] = None,
    ) -> SecurityGate:
        """Create a security gate"""
        gate = SecurityGate(
            sdlc_project_id=sdlc_project_id,
            phase_id=phase_id,
            gate_name=gate_name,
            gate_description=gate_description,
            gate_type=gate_type,
            requirements=requirements,
            status=SecurityGateStatus.PENDING.value,
        )
        self.db.add(gate)
        self.db.commit()
        self.db.refresh(gate)
        return gate
    
    def evaluate_security_gate(
        self,
        gate_id: int,
        requirements_met: List[str],
        reviewed_by: str,
        review_notes: Optional[str] = None,
        waiver_required: bool = False,
    ) -> SecurityGate:
        """Evaluate a security gate"""
        gate = self.db.query(SecurityGate).filter(SecurityGate.id == gate_id).first()
        if not gate:
            raise ValueError(f"Security gate {gate_id} not found")
        
        gate.requirements_met = requirements_met
        gate.reviewed_by = reviewed_by
        gate.review_date = datetime.utcnow()
        gate.review_notes = review_notes
        
        # Check if all requirements are met
        all_requirements = gate.requirements or []
        if set(requirements_met) >= set(all_requirements):
            gate.status = SecurityGateStatus.PASSED.value
        else:
            gate.status = SecurityGateStatus.FAILED.value
        
        gate.waiver_required = waiver_required
        
        self.db.commit()
        self.db.refresh(gate)
        return gate
    
    def approve_gate_waiver(
        self,
        gate_id: int,
        approved_by: str,
        waiver_rationale: str,
    ) -> SecurityGate:
        """Approve a security gate waiver"""
        gate = self.db.query(SecurityGate).filter(SecurityGate.id == gate_id).first()
        if not gate:
            raise ValueError(f"Security gate {gate_id} not found")
        
        gate.waiver_approved = True
        gate.waiver_approved_by = approved_by
        gate.waiver_approval_date = datetime.utcnow()
        gate.waiver_rationale = waiver_rationale
        gate.status = SecurityGateStatus.WAIVED.value
        
        self.db.commit()
        self.db.refresh(gate)
        return gate
    
    def get_project_status(self, project_id: int) -> Dict[str, Any]:
        """Get comprehensive project status"""
        project = self.db.query(SDLCProject).filter(SDLCProject.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        phases = self.db.query(SDLCPhase).filter(
            SDLCPhase.sdlc_project_id == project_id
        ).order_by(SDLCPhase.phase_order).all()
        
        gates = self.db.query(SecurityGate).filter(
            SecurityGate.sdlc_project_id == project_id
        ).all()
        
        return {
            "project": project,
            "phases": phases,
            "security_gates": gates,
            "phase_summary": self._summarize_phases(phases),
            "gate_summary": self._summarize_gates(gates),
        }
    
    def _update_project_phase(self, project_id: int):
        """Update project current phase based on phase statuses"""
        project = self.db.query(SDLCProject).filter(SDLCProject.id == project_id).first()
        if not project:
            return
        
        phases = self.db.query(SDLCPhase).filter(
            SDLCPhase.sdlc_project_id == project_id
        ).order_by(SDLCPhase.phase_order).all()
        
        # Find current phase (first incomplete phase)
        for phase in phases:
            if phase.status != PhaseStatus.COMPLETED.value:
                project.current_phase = phase.phase_name
                if phase.status == PhaseStatus.IN_PROGRESS.value:
                    project.project_status = PhaseStatus.IN_PROGRESS.value
                break
        else:
            # All phases completed
            if phases:
                project.current_phase = phases[-1].phase_name
                project.project_status = PhaseStatus.COMPLETED.value
                project.actual_completion_date = datetime.utcnow()
        
        self.db.commit()
    
    def _summarize_phases(self, phases: List[SDLCPhase]) -> Dict[str, Any]:
        """Summarize phases"""
        return {
            "total": len(phases),
            "completed": sum(1 for p in phases if p.status == PhaseStatus.COMPLETED.value),
            "in_progress": sum(1 for p in phases if p.status == PhaseStatus.IN_PROGRESS.value),
            "not_started": sum(1 for p in phases if p.status == PhaseStatus.NOT_STARTED.value),
        }
    
    def _summarize_gates(self, gates: List[SecurityGate]) -> Dict[str, Any]:
        """Summarize security gates"""
        return {
            "total": len(gates),
            "passed": sum(1 for g in gates if g.status == SecurityGateStatus.PASSED.value),
            "failed": sum(1 for g in gates if g.status == SecurityGateStatus.FAILED.value),
            "waived": sum(1 for g in gates if g.status == SecurityGateStatus.WAIVED.value),
            "pending": sum(1 for g in gates if g.status == SecurityGateStatus.PENDING.value),
        }
