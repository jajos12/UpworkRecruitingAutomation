"""In-memory data manager with Google Sheets persistence."""

import uuid
from typing import Dict, List, Optional
from datetime import datetime
from backend.models import (
    JobCreate, JobResponse, JobCriteriaModel,
    ProposalCreate, ProposalResponse,
    AnalysisResult, FreelancerProfile
)


class DataManager:
    """
    Manages in-memory data store for jobs and proposals.
    
    Can be extended to persist to Google Sheets or other storage.
    """
    
    def __init__(self):
        """Initialize data store."""
        self.jobs: Dict[str, JobResponse] = {}
        self.proposals: Dict[str, ProposalResponse] = {}
        self.analysis_results: Dict[str, AnalysisResult] = {}
    
    # ========================================================================
    # Job Operations
    # ========================================================================
    
    def create_job(self, job_data: JobCreate, job_id: Optional[str] = None) -> JobResponse:
        """Create a new job posting."""
        if not job_id:
            job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        job = JobResponse(
            job_id=job_id,
            title=job_data.title,
            description=job_data.description,
            criteria=job_data.criteria,
            created_at=datetime.now()
        )
        
        self.jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[JobResponse]:
        """Get all jobs."""
        return list(self.jobs.values())
    
    def update_job_counts(self, job_id: str):
        """Update proposal counts for a job."""
        if job_id not in self.jobs:
            return
        
        proposals = self.get_proposals_for_job(job_id)
        
        self.jobs[job_id].proposal_count = len(proposals)
        self.jobs[job_id].tier1_count = sum(1 for p in proposals if p.ai_tier == 1)
        self.jobs[job_id].tier2_count = sum(1 for p in proposals if p.ai_tier == 2)
        self.jobs[job_id].tier3_count = sum(1 for p in proposals if p.ai_tier == 3)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job and all its proposals."""
        if job_id not in self.jobs:
            return False
        
        # Delete associated proposals
        proposal_ids = [p.proposal_id for p in self.proposals.values() if p.job_id == job_id]
        for proposal_id in proposal_ids:
            del self.proposals[proposal_id]
            if proposal_id in self.analysis_results:
                del self.analysis_results[proposal_id]
        
        del self.jobs[job_id]
        return True
    
    # ========================================================================
    # Proposal Operations
    # ========================================================================
    
    def create_proposal(self, proposal_data: ProposalCreate) -> ProposalResponse:
        """Create a new proposal."""
        proposal_id = f"proposal_{uuid.uuid4().hex[:12]}"
        
        proposal = ProposalResponse(
            proposal_id=proposal_id,
            job_id=proposal_data.job_id,
            freelancer=proposal_data.freelancer,
            cover_letter=proposal_data.cover_letter,
            bid_amount=proposal_data.bid_amount,
            estimated_duration=proposal_data.estimated_duration,
            screening_answers=proposal_data.screening_answers,
            created_at=datetime.now()
        )
        
        self.proposals[proposal_id] = proposal
        
        # Update job counts
        self.update_job_counts(proposal_data.job_id)
        
        return proposal
    
    def get_proposal(self, proposal_id: str) -> Optional[ProposalResponse]:
        """Get proposal by ID."""
        return self.proposals.get(proposal_id)
    
    def get_all_proposals(self) -> List[ProposalResponse]:
        """Get all proposals."""
        return list(self.proposals.values())
    
    def get_proposals_for_job(self, job_id: str) -> List[ProposalResponse]:
        """Get all proposals for a specific job."""
        return [p for p in self.proposals.values() if p.job_id == job_id]
    
    def update_proposal_analysis(self, proposal_id: str, analysis: AnalysisResult):
        """Update proposal with AI analysis results."""
        if proposal_id not in self.proposals:
            return
        
        proposal = self.proposals[proposal_id]
        proposal.ai_score = analysis.score
        proposal.ai_tier = analysis.tier
        proposal.ai_reasoning = analysis.reasoning
        proposal.status = f"tier{analysis.tier}"
        
        # Store detailed analysis
        self.analysis_results[proposal_id] = analysis
        
        # Update job counts
        self.update_job_counts(proposal.job_id)
    
    def delete_proposal(self, proposal_id: str) -> bool:
        """Delete a proposal."""
        if proposal_id not in self.proposals:
            return False
        
        job_id = self.proposals[proposal_id].job_id
        del self.proposals[proposal_id]
        
        if proposal_id in self.analysis_results:
            del self.analysis_results[proposal_id]
        
        # Update job counts
        self.update_job_counts(job_id)
        
        return True
    
    # ========================================================================
    # Analysis Operations
    # ========================================================================
    
    def get_analysis(self, proposal_id: str) -> Optional[AnalysisResult]:
        """Get analysis result for a proposal."""
        return self.analysis_results.get(proposal_id)
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    def get_stats(self) -> Dict:
        """Get overall statistics."""
        all_proposals = self.get_all_proposals()
        
        return {
            "total_jobs": len(self.jobs),
            "total_proposals": len(all_proposals),
            "tier1_count": sum(1 for p in all_proposals if p.ai_tier == 1),
            "tier2_count": sum(1 for p in all_proposals if p.ai_tier == 2),
            "tier3_count": sum(1 for p in all_proposals if p.ai_tier == 3),
            "pending_count": sum(1 for p in all_proposals if p.ai_score is None),
        }
    
    # ========================================================================
    # Utilities
    # ========================================================================
    
    def clear_all_data(self):
        """Clear all data (useful for testing)."""
        self.jobs.clear()
        self.proposals.clear()
        self.analysis_results.clear()
