"""
SA-5: Information System Documentation Service

FedRAMP SA-5 compliance service for:
- Documentation inventory
- Version control
- Distribution tracking
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    SystemDocumentation,
    DocumentationDistribution,
    DocumentationType,
    DocumentationStatus,
)


class SystemDocumentationService:
    """Service for SA-5: Information System Documentation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_documentation(
        self,
        document_name: str,
        document_type: DocumentationType,
        system_name: str,
        version: str = "1.0",
        document_description: Optional[str] = None,
        system_id: Optional[str] = None,
        document_location: Optional[str] = None,
        document_format: Optional[str] = None,
        author: Optional[str] = None,
        owner: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> SystemDocumentation:
        """Create new system documentation"""
        doc = SystemDocumentation(
            document_name=document_name,
            document_type=document_type.value,
            document_description=document_description,
            system_name=system_name,
            system_id=system_id,
            version=version,
            document_location=document_location,
            document_format=document_format,
            author=author,
            owner=owner,
            status=DocumentationStatus.DRAFT.value,
            classification=classification,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc
    
    def update_documentation_version(
        self,
        documentation_id: int,
        new_version: str,
        document_location: Optional[str] = None,
        changes: Optional[List[str]] = None,
    ) -> SystemDocumentation:
        """Create a new version of documentation"""
        doc = self.db.query(SystemDocumentation).filter(
            SystemDocumentation.id == documentation_id
        ).first()
        if not doc:
            raise ValueError(f"Documentation {documentation_id} not found")
        
        # Update version history
        version_history = doc.version_history or []
        version_history.append({
            "version": doc.version,
            "updated_date": doc.last_updated_date.isoformat() if doc.last_updated_date else None,
            "changes": changes or [],
        })
        
        doc.previous_version = doc.version
        doc.version = new_version
        doc.version_history = version_history
        doc.document_location = document_location or doc.document_location
        doc.last_updated_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(doc)
        return doc
    
    def approve_documentation(
        self,
        documentation_id: int,
        approved_by: str,
    ) -> SystemDocumentation:
        """Approve documentation"""
        doc = self.db.query(SystemDocumentation).filter(
            SystemDocumentation.id == documentation_id
        ).first()
        if not doc:
            raise ValueError(f"Documentation {documentation_id} not found")
        
        doc.status = DocumentationStatus.APPROVED.value
        doc.approved_by = approved_by
        doc.approval_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(doc)
        return doc
    
    def publish_documentation(
        self,
        documentation_id: int,
    ) -> SystemDocumentation:
        """Publish documentation"""
        doc = self.db.query(SystemDocumentation).filter(
            SystemDocumentation.id == documentation_id
        ).first()
        if not doc:
            raise ValueError(f"Documentation {documentation_id} not found")
        
        if doc.status != DocumentationStatus.APPROVED.value:
            raise ValueError("Documentation must be approved before publishing")
        
        doc.status = DocumentationStatus.PUBLISHED.value
        doc.published_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(doc)
        return doc
    
    def create_distribution(
        self,
        system_documentation_id: int,
        recipient_name: str,
        recipient_email: Optional[str] = None,
        recipient_role: Optional[str] = None,
        distribution_method: Optional[str] = None,
        distributed_by: Optional[str] = None,
    ) -> DocumentationDistribution:
        """Create a documentation distribution"""
        distribution = DocumentationDistribution(
            system_documentation_id=system_documentation_id,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            recipient_role=recipient_role,
            distribution_method=distribution_method,
            distributed_by=distributed_by,
            distribution_date=datetime.utcnow(),
        )
        self.db.add(distribution)
        
        # Update document distribution list
        doc = self.db.query(SystemDocumentation).filter(
            SystemDocumentation.id == system_documentation_id
        ).first()
        if doc:
            distribution_list = doc.distribution_list or []
            distribution_list.append({
                "recipient_name": recipient_name,
                "recipient_email": recipient_email,
                "distribution_date": distribution.distribution_date.isoformat(),
            })
            doc.distribution_list = distribution_list
        
        self.db.commit()
        self.db.refresh(distribution)
        return distribution
    
    def acknowledge_distribution(
        self,
        distribution_id: int,
    ) -> DocumentationDistribution:
        """Acknowledge receipt of documentation"""
        distribution = self.db.query(DocumentationDistribution).filter(
            DocumentationDistribution.id == distribution_id
        ).first()
        if not distribution:
            raise ValueError(f"Distribution {distribution_id} not found")
        
        distribution.acknowledged = True
        distribution.acknowledgment_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(distribution)
        return distribution
    
    def record_access(
        self,
        distribution_id: int,
    ) -> DocumentationDistribution:
        """Record access to documentation"""
        distribution = self.db.query(DocumentationDistribution).filter(
            DocumentationDistribution.id == distribution_id
        ).first()
        if not distribution:
            raise ValueError(f"Distribution {distribution_id} not found")
        
        distribution.last_accessed_date = datetime.utcnow()
        distribution.access_count = (distribution.access_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(distribution)
        return distribution
    
    def list_documentation(
        self,
        system_name: Optional[str] = None,
        document_type: Optional[DocumentationType] = None,
        status: Optional[DocumentationStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[SystemDocumentation], int]:
        """List system documentation"""
        query = self.db.query(SystemDocumentation)
        
        if system_name:
            query = query.filter(SystemDocumentation.system_name == system_name)
        
        if document_type:
            query = query.filter(SystemDocumentation.document_type == document_type.value)
        
        if status:
            query = query.filter(SystemDocumentation.status == status.value)
        
        total = query.count()
        docs = query.order_by(desc(SystemDocumentation.created_date)).offset(offset).limit(limit).all()
        
        return docs, total
    
    def get_documentation_summary(self, system_name: Optional[str] = None) -> Dict[str, Any]:
        """Get documentation summary"""
        query = self.db.query(SystemDocumentation)
        
        if system_name:
            query = query.filter(SystemDocumentation.system_name == system_name)
        
        docs = query.all()
        
        return {
            "total_documents": len(docs),
            "by_type": self._summarize_by_type(docs),
            "by_status": self._summarize_by_status(docs),
            "distribution_summary": self._get_distribution_summary(docs),
        }
    
    def _summarize_by_type(self, docs: List[SystemDocumentation]) -> Dict[str, int]:
        """Summarize by document type"""
        summary = {}
        for doc in docs:
            doc_type = doc.document_type
            summary[doc_type] = summary.get(doc_type, 0) + 1
        return summary
    
    def _summarize_by_status(self, docs: List[SystemDocumentation]) -> Dict[str, int]:
        """Summarize by status"""
        summary = {}
        for doc in docs:
            status = doc.status
            summary[status] = summary.get(status, 0) + 1
        return summary
    
    def _get_distribution_summary(self, docs: List[SystemDocumentation]) -> Dict[str, Any]:
        """Get distribution summary"""
        total_distributions = 0
        acknowledged = 0
        
        for doc in docs:
            distributions = self.db.query(DocumentationDistribution).filter(
                DocumentationDistribution.system_documentation_id == doc.id
            ).all()
            total_distributions += len(distributions)
            acknowledged += sum(1 for d in distributions if d.acknowledged)
        
        return {
            "total_distributions": total_distributions,
            "acknowledged": acknowledged,
            "pending_acknowledgment": total_distributions - acknowledged,
        }
