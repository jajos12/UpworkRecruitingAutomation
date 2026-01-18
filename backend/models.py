"""Pydantic models for API request/response validation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Job Models
# ============================================================================

class JobCriteriaModel(BaseModel):
    """Hiring criteria for a job."""
    must_have: List[str] = Field(default_factory=list, description="Hard requirements")
    nice_to_have: List[Dict[str, Any]] = Field(default_factory=list, description="Weighted preferences")
    red_flags: List[str] = Field(default_factory=list, description="Warning signs")


class JobCreate(BaseModel):
    """Request model for creating a job posting."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    criteria: Optional[JobCriteriaModel] = None


class JobResponse(BaseModel):
    """Response model for job posting."""
    job_id: str
    title: str
    description: str
    criteria: Optional[JobCriteriaModel]
    proposal_count: int = 0
    tier1_count: int = 0
    tier2_count: int = 0
    tier3_count: int = 0
    created_at: datetime


# ============================================================================
# Freelancer Models
# ============================================================================

class FreelancerProfile(BaseModel):
    """Freelancer profile information."""
    freelancer_id: str
    name: str
    title: str
    hourly_rate: Optional[float] = None
    job_success_score: Optional[int] = None
    total_earnings: Optional[float] = None
    top_rated_status: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    bio: Optional[str] = Field(None, description="Freelancer's summary/overview")
    certifications: List[str] = Field(default_factory=list, description="Formal credentials")
    portfolio_items: List[Dict[str, str]] = Field(default_factory=list, description="Work samples (title, desc)")
    work_history_summary: Optional[str] = None
    profile_url: Optional[str] = None


# ============================================================================
# Proposal Models
# ============================================================================

class ProposalCreate(BaseModel):
    """Request model for creating a proposal."""
    job_id: str
    freelancer: FreelancerProfile
    cover_letter: str = Field(..., min_length=10)
    bid_amount: float = Field(..., gt=0)
    estimated_duration: Optional[str] = None
    screening_answers: Optional[str] = None


class ProposalResponse(BaseModel):
    """Response model for proposal."""
    proposal_id: str
    job_id: str
    freelancer: FreelancerProfile
    cover_letter: str
    bid_amount: float
    estimated_duration: Optional[str]
    screening_answers: Optional[str]
    ai_score: Optional[int] = None
    ai_tier: Optional[int] = None
    ai_reasoning: Optional[str] = None
    status: str = "pending"  # pending, tier1, tier2, tier3
    created_at: datetime


# ============================================================================
# Analysis Models
# ============================================================================

class AnalysisResult(BaseModel):
    """AI analysis result for a proposal."""
    proposal_id: str
    score: int = Field(..., ge=0, le=100)
    tier: int = Field(..., ge=1, le=3)
    reasoning: str
    recommendation: str  # ADVANCE, REVIEW, REJECT
    red_flags: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)


# ============================================================================
# Pipeline Models
# ============================================================================

class PipelineRunRequest(BaseModel):
    """Request to run pipeline."""
    fetch: bool = True
    analyze: bool = True
    communicate: bool = True
    dry_run: bool = False
    job_id: Optional[str] = None  # If None, process all jobs


class PipelineStatus(BaseModel):
    """Pipeline execution status."""
    running: bool
    current_phase: Optional[str] = None  # fetch, analyze, communicate
    progress: float = 0.0  # 0.0 to 1.0
    message: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=dict)


class DaemonStatus(BaseModel):
    """Daemon status."""
    running: bool
    interval_minutes: int = 15
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


# ============================================================================
# WebSocket Models
# ============================================================================

class ActivityEvent(BaseModel):
    """Real-time activity event."""
    timestamp: datetime
    event_type: str  # pipeline_start, pipeline_end, analysis_complete, message_sent, etc.
    message: str
    data: Optional[Dict[str, Any]] = None


class ProgressEvent(BaseModel):
    """Pipeline progress event."""
    phase: str
    progress: float  # 0.0 to 1.0
    message: str
