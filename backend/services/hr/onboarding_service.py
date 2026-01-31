"""
Onboarding Service
Handles new hire workflows, document collection, and onboarding checklists
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from collections import defaultdict
from enum import Enum

from models.hr_personnel import (
    Personnel,
    EmploymentStatus,
    EmployeeDocument,
    Certification,
    CertificationStatus
)
from utils.tenancy import scoped_query


class OnboardingStatus(str, Enum):
    """Onboarding status enum"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class OnboardingService:
    """Service for managing employee onboarding workflows"""

    # Standard onboarding checklist templates
    STANDARD_CHECKLIST = [
        {"task": "Complete I-9 Form", "category": "documents", "required": True, "deadline_days": 3},
        {"task": "Complete W-4 Form", "category": "documents", "required": True, "deadline_days": 3},
        {"task": "Upload Driver's License", "category": "documents", "required": True, "deadline_days": 1},
        {"task": "Background Check Authorization", "category": "documents", "required": True, "deadline_days": 1},
        {"task": "Direct Deposit Setup", "category": "payroll", "required": True, "deadline_days": 7},
        {"task": "Emergency Contact Information", "category": "personal", "required": True, "deadline_days": 3},
        {"task": "Benefits Enrollment", "category": "benefits", "required": False, "deadline_days": 30},
        {"task": "Company Handbook Review", "category": "training", "required": True, "deadline_days": 7},
        {"task": "IT Account Setup", "category": "it", "required": True, "deadline_days": 1},
        {"task": "Uniform/Equipment Issue", "category": "equipment", "required": True, "deadline_days": 7},
        {"task": "Station Orientation", "category": "training", "required": True, "deadline_days": 14},
        {"task": "Safety Training", "category": "training", "required": True, "deadline_days": 14},
    ]

    EMS_CHECKLIST = [
        {"task": "EMT/Paramedic Certification Upload", "category": "certifications", "required": True, "deadline_days": 1},
        {"task": "CPR Certification Upload", "category": "certifications", "required": True, "deadline_days": 1},
        {"task": "ACLS Certification Upload", "category": "certifications", "required": False, "deadline_days": 7},
        {"task": "PALS Certification Upload", "category": "certifications", "required": False, "deadline_days": 7},
        {"task": "Vehicle Orientation", "category": "training", "required": True, "deadline_days": 7},
        {"task": "Radio Communication Training", "category": "training", "required": True, "deadline_days": 7},
        {"task": "Medical Protocols Review", "category": "training", "required": True, "deadline_days": 14},
        {"task": "Field Training Officer Assignment", "category": "training", "required": True, "deadline_days": 3},
    ]

    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id

    async def get_onboarding_checklist(
        self,
        job_title: str
    ) -> List[Dict[str, Any]]:
        """
        Get onboarding checklist template based on job title
        Returns combined standard + role-specific items
        """
        checklist = self.STANDARD_CHECKLIST.copy()

        # Add role-specific items
        if any(role in job_title.lower() for role in ["emt", "paramedic", "medic", "ems"]):
            checklist.extend(self.EMS_CHECKLIST)

        return checklist

    async def create_onboarding_record(
        self,
        personnel_id: int
    ) -> Dict[str, Any]:
        """
        Create onboarding record for a new hire
        Generates checklist and tracks progress
        """
        personnel = scoped_query(self.db, Personnel, self.org_id).filter(
            Personnel.id == personnel_id
        ).first()

        if not personnel:
            raise ValueError("Personnel not found")

        checklist = await self.get_onboarding_checklist(personnel.job_title)

        # Calculate deadline for each task
        tasks_with_deadlines = []
        for task in checklist:
            deadline = personnel.hire_date + timedelta(days=task["deadline_days"])
            tasks_with_deadlines.append({
                **task,
                "deadline": deadline,
                "completed": False,
                "completed_date": None
            })

        # In a real implementation, this would be stored in a dedicated onboarding table
        # For now, we'll return the structure
        return {
            "personnel_id": personnel_id,
            "employee_id": personnel.employee_id,
            "name": f"{personnel.first_name} {personnel.last_name}",
            "job_title": personnel.job_title,
            "hire_date": personnel.hire_date.isoformat(),
            "onboarding_status": self._calculate_onboarding_status(tasks_with_deadlines),
            "tasks": tasks_with_deadlines,
            "progress": self._calculate_progress(tasks_with_deadlines)
        }

    def _calculate_onboarding_status(
        self,
        tasks: List[Dict[str, Any]]
    ) -> str:
        """Calculate overall onboarding status"""
        if not tasks:
            return OnboardingStatus.NOT_STARTED.value

        completed = [t for t in tasks if t["completed"]]
        required_tasks = [t for t in tasks if t["required"]]
        required_completed = [t for t in required_tasks if t["completed"]]

        # Check if any required tasks are overdue
        today = date.today()
        overdue = [
            t for t in required_tasks
            if not t["completed"] and t["deadline"] < today
        ]

        if overdue:
            return OnboardingStatus.OVERDUE.value
        elif len(required_completed) == len(required_tasks):
            return OnboardingStatus.COMPLETED.value
        elif completed:
            return OnboardingStatus.IN_PROGRESS.value
        else:
            return OnboardingStatus.NOT_STARTED.value

    def _calculate_progress(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate onboarding progress statistics"""
        total = len(tasks)
        completed = sum(1 for t in tasks if t["completed"])
        required = sum(1 for t in tasks if t["required"])
        required_completed = sum(1 for t in tasks if t["required"] and t["completed"])

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "required_tasks": required,
            "required_completed": required_completed,
            "overall_percentage": (completed / total * 100) if total > 0 else 0,
            "required_percentage": (required_completed / required * 100) if required > 0 else 0
        }

    async def get_new_hires(
        self,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get all new hires from the last X days
        Includes onboarding status
        """
        cutoff_date = date.today() - timedelta(days=days)
        
        new_hires = scoped_query(self.db, Personnel, self.org_id).filter(
            and_(
                Personnel.hire_date >= cutoff_date,
                Personnel.employment_status == EmploymentStatus.ACTIVE
            )
        ).order_by(Personnel.hire_date.desc()).all()

        # Get all personnel IDs
        personnel_ids = [person.id for person in new_hires]
        
        # Load all documents in a single query grouped by personnel_id
        if personnel_ids:
            documents = scoped_query(self.db, EmployeeDocument, self.org_id).filter(
                EmployeeDocument.personnel_id.in_(personnel_ids)
            ).all()
            doc_counts = defaultdict(int)
            for doc in documents:
                doc_counts[doc.personnel_id] += 1
            
            # Load all certifications in a single query grouped by personnel_id
            certifications = scoped_query(self.db, Certification, self.org_id).filter(
                Certification.personnel_id.in_(personnel_ids)
            ).all()
            cert_counts = defaultdict(int)
            for cert in certifications:
                cert_counts[cert.personnel_id] += 1
        else:
            doc_counts = defaultdict(int)
            cert_counts = defaultdict(int)

        result = []
        for person in new_hires:
            # Get counts from pre-loaded dictionaries
            doc_count = doc_counts.get(person.id, 0)
            cert_count = cert_counts.get(person.id, 0)

            days_since_hire = (date.today() - person.hire_date).days

            result.append({
                "personnel_id": person.id,
                "employee_id": person.employee_id,
                "name": f"{person.first_name} {person.last_name}",
                "job_title": person.job_title,
                "department": person.department,
                "hire_date": person.hire_date.isoformat(),
                "days_since_hire": days_since_hire,
                "documents_uploaded": doc_count,
                "certifications_uploaded": cert_count,
                "estimated_completion": self._estimate_onboarding_completion(
                    doc_count,
                    cert_count,
                    person.job_title
                )
            })

        return result

    def _estimate_onboarding_completion(
        self,
        doc_count: int,
        cert_count: int,
        job_title: str
    ) -> int:
        """Estimate onboarding completion percentage based on uploads"""
        checklist = self.STANDARD_CHECKLIST.copy()
        
        if any(role in job_title.lower() for role in ["emt", "paramedic", "medic", "ems"]):
            checklist.extend(self.EMS_CHECKLIST)

        doc_tasks = sum(1 for t in checklist if t["category"] in ["documents", "certifications"])
        
        if doc_tasks == 0:
            return 100

        # Simple estimation: assume each doc/cert covers one task
        estimated_completed = min(doc_count + cert_count, doc_tasks)
        return int((estimated_completed / len(checklist)) * 100)

    async def get_pending_documents(
        self,
        personnel_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of pending/missing documents for new hires
        """
        # Get new hires from last 90 days
        new_hires = await self.get_new_hires(90)

        if personnel_id:
            new_hires = [h for h in new_hires if h["personnel_id"] == personnel_id]

        result = []
        for hire in new_hires:
            # Get existing documents
            existing_docs = scoped_query(self.db, EmployeeDocument, self.org_id).filter(
                EmployeeDocument.personnel_id == hire["personnel_id"]
            ).all()

            existing_types = {doc.document_type for doc in existing_docs}

            # Required document types
            required_docs = [
                "I-9", "W-4", "Driver's License", "Background Check",
                "Emergency Contact", "Direct Deposit"
            ]

            missing = [doc for doc in required_docs if doc not in existing_types]

            if missing:
                result.append({
                    "personnel_id": hire["personnel_id"],
                    "employee_id": hire["employee_id"],
                    "name": hire["name"],
                    "hire_date": hire["hire_date"],
                    "days_since_hire": hire["days_since_hire"],
                    "missing_documents": missing,
                    "urgency": "high" if hire["days_since_hire"] > 7 else "normal"
                })

        return result

    async def upload_document(
        self,
        personnel_id: int,
        document_type: str,
        document_name: str,
        document_path: str,
        uploaded_by: str,
        expiration_date: Optional[date] = None,
        confidential: bool = False
    ) -> EmployeeDocument:
        """Upload a document for a personnel member"""
        personnel = scoped_query(self.db, Personnel, self.org_id).filter(
            Personnel.id == personnel_id
        ).first()

        if not personnel:
            raise ValueError("Personnel not found")

        document = EmployeeDocument(
            org_id=self.org_id,
            personnel_id=personnel_id,
            document_type=document_type,
            document_name=document_name,
            document_path=document_path,
            uploaded_by=uploaded_by,
            expiration_date=expiration_date,
            confidential=confidential,
            uploaded_at=datetime.utcnow()
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    async def get_personnel_documents(
        self,
        personnel_id: int
    ) -> List[EmployeeDocument]:
        """Get all documents for a personnel member"""
        return scoped_query(self.db, EmployeeDocument, self.org_id).filter(
            EmployeeDocument.personnel_id == personnel_id
        ).order_by(EmployeeDocument.uploaded_at.desc()).all()

    async def get_expiring_documents(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get documents expiring within specified days"""
        expiry_date = date.today() + timedelta(days=days)
        
        expiring = scoped_query(self.db, EmployeeDocument, self.org_id).filter(
            and_(
                EmployeeDocument.expiration_date.isnot(None),
                EmployeeDocument.expiration_date <= expiry_date,
                EmployeeDocument.expiration_date >= date.today()
            )
        ).all()

        result = []
        for doc in expiring:
            personnel = scoped_query(self.db, Personnel, self.org_id).filter(
                Personnel.id == doc.personnel_id
            ).first()

            if personnel:
                result.append({
                    "document_id": doc.id,
                    "personnel_id": personnel.id,
                    "employee_id": personnel.employee_id,
                    "name": f"{personnel.first_name} {personnel.last_name}",
                    "document_type": doc.document_type,
                    "document_name": doc.document_name,
                    "expiration_date": doc.expiration_date.isoformat(),
                    "days_until_expiration": (doc.expiration_date - date.today()).days
                })

        return sorted(result, key=lambda x: x["days_until_expiration"])

    async def get_onboarding_analytics(self) -> Dict[str, Any]:
        """
        Generate analytics on onboarding status
        """
        new_hires = await self.get_new_hires(90)
        
        if not new_hires:
            return {
                "total_new_hires": 0,
                "message": "No new hires in the last 90 days"
            }

        # Categorize by completion estimate
        by_completion = {
            "0-25%": 0,
            "26-50%": 0,
            "51-75%": 0,
            "76-100%": 0
        }

        for hire in new_hires:
            completion = hire["estimated_completion"]
            if completion <= 25:
                by_completion["0-25%"] += 1
            elif completion <= 50:
                by_completion["26-50%"] += 1
            elif completion <= 75:
                by_completion["51-75%"] += 1
            else:
                by_completion["76-100%"] += 1

        # Calculate average time to complete
        completed = [h for h in new_hires if h["estimated_completion"] >= 90]
        avg_days = (
            sum(h["days_since_hire"] for h in completed) / len(completed)
            if completed else None
        )

        return {
            "total_new_hires": len(new_hires),
            "by_completion": by_completion,
            "average_days_to_complete": avg_days,
            "pending_documents": len(await self.get_pending_documents()),
            "recent_hires": new_hires[:10]  # Top 10 most recent
        }

    async def send_onboarding_reminder(
        self,
        personnel_id: int
    ) -> Dict[str, Any]:
        """
        Generate onboarding reminder for a personnel member
        Returns what they still need to complete
        """
        personnel = scoped_query(self.db, Personnel, self.org_id).filter(
            Personnel.id == personnel_id
        ).first()

        if not personnel:
            raise ValueError("Personnel not found")

        # Get existing documents
        existing_docs = await self.get_personnel_documents(personnel_id)
        existing_types = {doc.document_type for doc in existing_docs}

        # Get existing certifications
        existing_certs = scoped_query(self.db, Certification, self.org_id).filter(
            Certification.personnel_id == personnel_id
        ).all()

        # Get checklist
        checklist = await self.get_onboarding_checklist(personnel.job_title)

        # Identify pending items
        pending_items = []
        for item in checklist:
            is_complete = False
            
            # Simple check based on category
            if item["category"] == "documents":
                # Check if related document exists
                is_complete = any(
                    item["task"].lower() in doc_type.lower()
                    for doc_type in existing_types
                )
            elif item["category"] == "certifications":
                # Check if related cert exists
                is_complete = len(existing_certs) > 0

            if not is_complete:
                deadline = personnel.hire_date + timedelta(days=item["deadline_days"])
                days_remaining = (deadline - date.today()).days
                
                pending_items.append({
                    "task": item["task"],
                    "category": item["category"],
                    "required": item["required"],
                    "deadline": deadline.isoformat(),
                    "days_remaining": days_remaining,
                    "overdue": days_remaining < 0
                })

        return {
            "personnel_id": personnel_id,
            "employee_id": personnel.employee_id,
            "name": f"{personnel.first_name} {personnel.last_name}",
            "hire_date": personnel.hire_date.isoformat(),
            "days_since_hire": (date.today() - personnel.hire_date).days,
            "pending_items": pending_items,
            "overdue_items": [i for i in pending_items if i["overdue"]],
            "required_pending": [i for i in pending_items if i["required"]]
        }

    async def get_onboarding_dashboard(self) -> Dict[str, Any]:
        """
        Comprehensive onboarding dashboard
        Shows overview of all new hires and their status
        """
        new_hires = await self.get_new_hires(90)
        pending_docs = await self.get_pending_documents()
        analytics = await self.get_onboarding_analytics()

        # Identify at-risk hires (>30 days and <50% complete)
        at_risk = [
            h for h in new_hires
            if h["days_since_hire"] > 30 and h["estimated_completion"] < 50
        ]

        return {
            "summary": {
                "total_new_hires": len(new_hires),
                "at_risk": len(at_risk),
                "pending_documents": len(pending_docs),
                "avg_completion": (
                    sum(h["estimated_completion"] for h in new_hires) / len(new_hires)
                    if new_hires else 0
                )
            },
            "analytics": analytics,
            "at_risk_hires": at_risk,
            "recent_hires": new_hires[:5]
        }
