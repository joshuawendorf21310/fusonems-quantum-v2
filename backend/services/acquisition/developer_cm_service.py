"""
SA-10: Developer Configuration Management Service

FedRAMP SA-10 compliance service for:
- Source code version control tracking
- Build management
- Release management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.acquisition import (
    SourceCodeRepository,
    CodeBranch,
    Build,
    Release,
    CMStatus,
    BuildStatus,
    ReleaseStatus,
)


class DeveloperCMService:
    """Service for SA-10: Developer Configuration Management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_repository(
        self,
        repository_name: str,
        repository_url: str,
        system_name: str,
        repository_type: str = "git",
        system_id: Optional[str] = None,
        access_restrictions: Optional[List[str]] = None,
        authorized_users: Optional[List[str]] = None,
    ) -> SourceCodeRepository:
        """Create a source code repository"""
        repo = SourceCodeRepository(
            repository_name=repository_name,
            repository_url=repository_url,
            repository_type=repository_type,
            system_name=system_name,
            system_id=system_id,
            access_restrictions=access_restrictions,
            authorized_users=authorized_users,
            status=CMStatus.ACTIVE.value,
        )
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)
        return repo
    
    def create_branch(
        self,
        source_code_repository_id: int,
        branch_name: str,
        branch_type: str,
        base_branch: Optional[str] = None,
        protected: bool = False,
        requires_review: bool = False,
        requires_approval: bool = False,
    ) -> CodeBranch:
        """Create a code branch"""
        branch = CodeBranch(
            source_code_repository_id=source_code_repository_id,
            branch_name=branch_name,
            branch_type=branch_type,
            base_branch=base_branch,
            protected=protected,
            requires_review=requires_review,
            requires_approval=requires_approval,
            status=CMStatus.ACTIVE.value,
        )
        self.db.add(branch)
        self.db.commit()
        self.db.refresh(branch)
        return branch
    
    def update_branch_commit(
        self,
        branch_id: int,
        latest_commit: str,
        commit_count: Optional[int] = None,
    ) -> CodeBranch:
        """Update branch with latest commit"""
        branch = self.db.query(CodeBranch).filter(CodeBranch.id == branch_id).first()
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")
        
        branch.latest_commit = latest_commit
        branch.last_commit_date = datetime.utcnow()
        if commit_count is not None:
            branch.commit_count = commit_count
        
        # Update repository last commit date
        repo = self.db.query(SourceCodeRepository).filter(
            SourceCodeRepository.id == branch.source_code_repository_id
        ).first()
        if repo:
            repo.last_commit_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(branch)
        return branch
    
    def create_build(
        self,
        source_code_repository_id: int,
        build_number: str,
        build_type: str,
        branch_id: Optional[int] = None,
        commit_hash: Optional[str] = None,
        branch_name: Optional[str] = None,
        build_configuration: Optional[Dict[str, Any]] = None,
    ) -> Build:
        """Create a build"""
        build = Build(
            source_code_repository_id=source_code_repository_id,
            branch_id=branch_id,
            build_number=build_number,
            build_type=build_type,
            commit_hash=commit_hash,
            branch_name=branch_name,
            build_configuration=build_configuration,
            status=BuildStatus.PENDING.value,
            started_at=datetime.utcnow(),
        )
        self.db.add(build)
        self.db.commit()
        self.db.refresh(build)
        return build
    
    def update_build_status(
        self,
        build_id: int,
        status: BuildStatus,
        build_output: Optional[str] = None,
        build_artifacts: Optional[List[str]] = None,
        tests_passed: Optional[int] = None,
        tests_failed: Optional[int] = None,
        security_scan_passed: Optional[bool] = None,
    ) -> Build:
        """Update build status"""
        build = self.db.query(Build).filter(Build.id == build_id).first()
        if not build:
            raise ValueError(f"Build {build_id} not found")
        
        build.status = status.value
        
        if status == BuildStatus.IN_PROGRESS:
            if not build.started_at:
                build.started_at = datetime.utcnow()
        elif status in [BuildStatus.SUCCESS, BuildStatus.FAILED]:
            build.completed_at = datetime.utcnow()
            if build.started_at:
                duration = (build.completed_at - build.started_at).total_seconds()
                build.duration_seconds = int(duration)
        
        if build_output:
            build.build_output = build_output
        
        if build_artifacts:
            build.build_artifacts = build_artifacts
        
        if tests_passed is not None:
            build.tests_passed = tests_passed
        
        if tests_failed is not None:
            build.tests_failed = tests_failed
        
        if security_scan_passed is not None:
            build.security_scan_passed = security_scan_passed
        
        self.db.commit()
        self.db.refresh(build)
        return build
    
    def create_release(
        self,
        release_name: str,
        release_version: str,
        system_name: str,
        build_id: Optional[int] = None,
        system_id: Optional[str] = None,
        release_description: Optional[str] = None,
        release_notes: Optional[str] = None,
        changes: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Release:
        """Create a release"""
        release = Release(
            release_name=release_name,
            release_version=release_version,
            release_description=release_description,
            system_name=system_name,
            system_id=system_id,
            build_id=build_id,
            release_notes=release_notes,
            changes=changes,
            dependencies=dependencies,
            status=ReleaseStatus.PLANNED.value,
        )
        self.db.add(release)
        self.db.commit()
        self.db.refresh(release)
        return release
    
    def approve_release(
        self,
        release_id: int,
        approved_by: str,
    ) -> Release:
        """Approve a release"""
        release = self.db.query(Release).filter(Release.id == release_id).first()
        if not release:
            raise ValueError(f"Release {release_id} not found")
        
        release.approved = True
        release.approved_by = approved_by
        release.approval_date = datetime.utcnow()
        release.status = ReleaseStatus.READY_FOR_RELEASE.value
        
        self.db.commit()
        self.db.refresh(release)
        return release
    
    def deploy_release(
        self,
        release_id: int,
        deployed_by: str,
        deployment_environment: str,
    ) -> Release:
        """Deploy a release"""
        release = self.db.query(Release).filter(Release.id == release_id).first()
        if not release:
            raise ValueError(f"Release {release_id} not found")
        
        if not release.approved:
            raise ValueError("Release must be approved before deployment")
        
        release.status = ReleaseStatus.RELEASED.value
        release.deployed_by = deployed_by
        release.deployment_date = datetime.utcnow()
        release.deployment_environment = deployment_environment
        release.released_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(release)
        return release
    
    def list_repositories(
        self,
        system_name: Optional[str] = None,
        status: Optional[CMStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[SourceCodeRepository], int]:
        """List source code repositories"""
        query = self.db.query(SourceCodeRepository)
        
        if system_name:
            query = query.filter(SourceCodeRepository.system_name == system_name)
        
        if status:
            query = query.filter(SourceCodeRepository.status == status.value)
        
        total = query.count()
        repos = query.order_by(desc(SourceCodeRepository.created_at)).offset(offset).limit(limit).all()
        
        return repos, total
    
    def get_repository_summary(self, repository_id: int) -> Dict[str, Any]:
        """Get comprehensive repository summary"""
        repo = self.db.query(SourceCodeRepository).filter(
            SourceCodeRepository.id == repository_id
        ).first()
        if not repo:
            raise ValueError(f"Repository {repository_id} not found")
        
        branches = self.db.query(CodeBranch).filter(
            CodeBranch.source_code_repository_id == repository_id
        ).all()
        
        builds = self.db.query(Build).filter(
            Build.source_code_repository_id == repository_id
        ).order_by(desc(Build.started_at)).limit(10).all()
        
        return {
            "repository": repo,
            "branches": branches,
            "recent_builds": builds,
            "branch_summary": self._summarize_branches(branches),
            "build_summary": self._summarize_builds(builds),
        }
    
    def _summarize_branches(self, branches: List[CodeBranch]) -> Dict[str, Any]:
        """Summarize branches"""
        return {
            "total": len(branches),
            "active": sum(1 for b in branches if b.status == CMStatus.ACTIVE.value),
            "protected": sum(1 for b in branches if b.protected),
        }
    
    def _summarize_builds(self, builds: List[Build]) -> Dict[str, Any]:
        """Summarize builds"""
        return {
            "total": len(builds),
            "success": sum(1 for b in builds if b.status == BuildStatus.SUCCESS.value),
            "failed": sum(1 for b in builds if b.status == BuildStatus.FAILED.value),
            "in_progress": sum(1 for b in builds if b.status == BuildStatus.IN_PROGRESS.value),
        }
