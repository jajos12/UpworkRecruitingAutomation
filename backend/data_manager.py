"""Database-backed data manager with SQLAlchemy persistence."""

import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import (
    JobCreate, JobResponse, JobCriteriaModel,
    ProposalCreate, ProposalResponse,
    AnalysisResult, FreelancerProfile
)
from backend.database import SessionLocal
from backend.database_models import Job as JobModel, Proposal as ProposalModel


class DataManager:
    """
    Manages database persistence for jobs and proposals.
    
    Uses SQLAlchemy for persistent storage in SQLite.
    """
    
    def __init__(self):
        """Initialize data manager."""
        pass
    
    def _get_db(self) -> Session:
        """Get database session."""
        return SessionLocal()
    
    # ========================================================================
    # Job Operations
    # ========================================================================
    
    def create_job(self, job_data: JobCreate, job_id: Optional[str] = None) -> JobResponse:
        """Create a new job posting."""
        db = self._get_db()
        try:
            if not job_id:
                job_id = f"job_{uuid.uuid4().hex[:12]}"
            
            # Convert Pydantic model to dict for JSON storage
            criteria_dict = job_data.criteria.model_dump() if job_data.criteria else None
            
            job_model = JobModel(
                job_id=job_id,
                title=job_data.title,
                description=job_data.description,
                criteria=criteria_dict,
                created_at=datetime.utcnow()
            )
            
            db.add(job_model)
            db.commit()
            db.refresh(job_model)
            
            return self._job_model_to_response(job_model)
        finally:
            db.close()
    
    def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Get job by ID."""
        db = self._get_db()
        try:
            job_model = db.query(JobModel).filter(JobModel.job_id == job_id).first()
            if not job_model:
                return None
            return self._job_model_to_response(job_model)
        finally:
            db.close()
    
    def get_all_jobs(self) -> List[JobResponse]:
        """Get all jobs."""
        db = self._get_db()
        try:
            jobs = db.query(JobModel).all()
            return [self._job_model_to_response(j) for j in jobs]
        finally:
            db.close()
    
    def update_job_counts(self, job_id: str):
        """Update proposal counts for a job."""
        db = self._get_db()
        try:
            job_model = db.query(JobModel).filter(JobModel.job_id == job_id).first()
            if not job_model:
                return
            
            proposals = db.query(ProposalModel).filter(ProposalModel.job_id == job_id).all()
            
            job_model.proposal_count = len(proposals)
            job_model.tier1_count = sum(1 for p in proposals if p.ai_tier == 1)
            job_model.tier2_count = sum(1 for p in proposals if p.ai_tier == 2)
            job_model.tier3_count = sum(1 for p in proposals if p.ai_tier == 3)
            
            db.commit()
        finally:
            db.close()
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job and all its proposals."""
        db = self._get_db()
        try:
            job_model = db.query(JobModel).filter(JobModel.job_id == job_id).first()
            if not job_model:
                return False
            
            db.delete(job_model)  # Cascade will delete proposals
            db.commit()
            return True
        finally:
            db.close()
    
    # ========================================================================
    # Proposal Operations
    # ========================================================================
    
    def create_proposal(self, proposal_data: ProposalCreate) -> ProposalResponse:
        """Create a new proposal."""
        db = self._get_db()
        try:
            proposal_id = f"proposal_{uuid.uuid4().hex[:12]}"
            
            # Convert FreelancerProfile to dict
            freelancer_dict = proposal_data.freelancer.model_dump()
            
            proposal_model =ProposalModel(
                proposal_id=proposal_id,
                job_id=proposal_data.job_id,
                freelancer=freelancer_dict,
                cover_letter=proposal_data.cover_letter,
                bid_amount=proposal_data.bid_amount,
                estimated_duration=proposal_data.estimated_duration,
                screening_answers=proposal_data.screening_answers,
                status="pending",
                created_at=datetime.utcnow()
            )
            
            db.add(proposal_model)
            db.commit()
            db.refresh(proposal_model)
            
            # Update job counts
            self.update_job_counts(proposal_data.job_id)
            
            return self._proposal_model_to_response(proposal_model)
        finally:
            db.close()
    
    def get_proposal(self, proposal_id: str) -> Optional[ProposalResponse]:
        """Get proposal by ID."""
        db = self._get_db()
        try:
            proposal_model = db.query(ProposalModel).filter(
                ProposalModel.proposal_id == proposal_id
            ).first()
            if not proposal_model:
                return None
            return self._proposal_model_to_response(proposal_model)
        finally:
            db.close()
    
    def get_all_proposals(self) -> List[ProposalResponse]:
        """Get all proposals."""
        db = self._get_db()
        try:
            proposals = db.query(ProposalModel).all()
            return [self._proposal_model_to_response(p) for p in proposals]
        finally:
            db.close()
    
    def get_proposals_for_job(self, job_id: str) -> List[ProposalResponse]:
        """Get all proposals for a specific job."""
        db = self._get_db()
        try:
            proposals = db.query(ProposalModel).filter(
                ProposalModel.job_id == job_id
            ).all()
            return [self._proposal_model_to_response(p) for p in proposals]
        finally:
            db.close()
    
    def update_proposal_analysis(self, proposal_id: str, analysis: AnalysisResult):
        """Update proposal with AI analysis results."""
        db = self._get_db()
        try:
            proposal_model = db.query(ProposalModel).filter(
                ProposalModel.proposal_id == proposal_id
            ).first()
            
            if not proposal_model:
                return
            
            proposal_model.ai_score = analysis.score
            proposal_model.ai_tier = analysis.tier
            proposal_model.ai_reasoning = analysis.reasoning
            proposal_model.ai_recommendation = analysis.recommendation
            proposal_model.ai_red_flags = analysis.red_flags
            proposal_model.ai_strengths = analysis.strengths
            proposal_model.status = f"tier{analysis.tier}"
            
            db.commit()
            
            # Update job counts
            self.update_job_counts(proposal_model.job_id)
        finally:
            db.close()
    
    def delete_proposal(self, proposal_id: str) -> bool:
        """Delete a proposal."""
        db = self._get_db()
        try:
            proposal_model = db.query(ProposalModel).filter(
                ProposalModel.proposal_id == proposal_id
            ).first()
            if not proposal_model:
                return False
            
            job_id = proposal_model.job_id
            db.delete(proposal_model)
            db.commit()
            
            # Update job counts
            self.update_job_counts(job_id)
            return True
        finally:
            db.close()
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    def get_stats(self) -> dict:
        """Get overall statistics."""
        db = self._get_db()
        try:
            total_jobs = db.query(JobModel).count()
            total_proposals = db.query(ProposalModel).count()
            
            tier1 = db.query(ProposalModel).filter(ProposalModel.ai_tier == 1).count()
            tier2 = db.query(ProposalModel).filter(ProposalModel.ai_tier == 2).count()
            tier3 = db.query(ProposalModel).filter(ProposalModel.ai_tier == 3).count()
            pending = db.query(ProposalModel).filter(ProposalModel.ai_tier == None).count()
            
            return {
                "total_jobs": total_jobs,
                "total_proposals": total_proposals,
                "tier1_count": tier1,
                "tier2_count": tier2,
                "tier3_count": tier3,
                "pending_count": pending
            }
        finally:
            db.close()
    
    def clear_all_data(self):
        """Clear all data (for testing)."""
        db = self._get_db()
        try:
            db.query(ProposalModel).delete()
            db.query(JobModel).delete()
            db.commit()
        finally:
            db.close()
    
    # ========================================================================
    # Conversion Helpers
    # ========================================================================
    
    def _job_model_to_response(self, job_model: JobModel) -> JobResponse:
        """Convert JobModel to JobResponse."""
        criteria = None
        if job_model.criteria:
            criteria = JobCriteriaModel(**job_model.criteria)
        
        return JobResponse(
            job_id=job_model.job_id,
            title=job_model.title,
            description=job_model.description,
            criteria=criteria,
            proposal_count=job_model.proposal_count,
            tier1_count=job_model.tier1_count,
            tier2_count=job_model.tier2_count,
            tier3_count=job_model.tier3_count,
            created_at=job_model.created_at
        )
    
    def _proposal_model_to_response(self, proposal_model: ProposalModel) -> ProposalResponse:
        """Convert ProposalModel to ProposalResponse."""
        freelancer = FreelancerProfile(**proposal_model.freelancer)
        
        return ProposalResponse(
            proposal_id=proposal_model.proposal_id,
            job_id=proposal_model.job_id,
            freelancer=freelancer,
            cover_letter=proposal_model.cover_letter,
            bid_amount=proposal_model.bid_amount,
            estimated_duration=proposal_model.estimated_duration,
            screening_answers=proposal_model.screening_answers,
            ai_score=proposal_model.ai_score,
            ai_tier=proposal_model.ai_tier,
            ai_reasoning=proposal_model.ai_reasoning,
            status=proposal_model.status,
            created_at=proposal_model.created_at
        )
