"""Pydantic models for API request/response validation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Auth Models
# ============================================================================

class LoginRequest(BaseModel):
    """Request model for login."""
    email: str
    password: str


# ============================================================================
# Job Models
# ============================================================================

class GenerateCriteriaRequest(BaseModel):
    """Request model for generating criteria from description."""
    description: str = Field(..., min_length=10)


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
    interview_questions: Optional[List['InterviewQuestion']] = None
    chat_history: Optional[List['ChatMessage']] = None

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

class InterviewGenerationConfig(BaseModel):
    """Configuration for generating interview questions."""
    behavioral_count: int = Field(1, ge=0, le=5, description="Number of behavioral questions")
    technical_count: int = Field(2, ge=0, le=10, description="Number of technical questions")
    red_flag_count: int = Field(1, ge=0, le=5, description="Number of red flag/gap questions")
    soft_skill_count: int = Field(1, ge=0, le=5, description="Number of soft skill/cultural questions")
    custom_focus: Optional[str] = Field(None, description="Specific topic to focus on")

class InterviewQuestion(BaseModel):
    """Generated interview question."""
    type: str  # Behavioral, Technical, Red Flag, Soft Skill
    question: str
    context: Optional[str] = None # Why ask this? / What to look for
    expected_answer: Optional[str] = None # Technical only

class InterviewGuide(BaseModel):
    """Full interview guide."""
    proposal_id: str
    questions: List[InterviewQuestion]

class ChatMessage(BaseModel):
    """Chat message for 'Chat with Resume'."""
    role: str # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    """Request query."""
    message: str


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


# ============================================================================
# Bulk Import Models
# ============================================================================

class BulkImportRequest(BaseModel):
    """Request to parse raw applicant data with AI."""
    job_id: str
    raw_text: str = Field(..., min_length=10, max_length=100000)
    input_format_hint: Optional[str] = Field(None, description="csv, markdown, plain, json, or auto")


class ParsedApplicant(BaseModel):
    """A single applicant parsed from raw text."""
    freelancer: FreelancerProfile
    cover_letter: str = ""
    bid_amount: float = 0.0
    estimated_duration: Optional[str] = None
    screening_answers: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Parsing confidence 0-1")
    parse_notes: List[str] = Field(default_factory=list, description="Warnings about this parse")


class BulkImportParseResponse(BaseModel):
    """Response from AI parsing of raw text."""
    applicants: List[ParsedApplicant]
    total_found: int
    parse_warnings: List[str] = Field(default_factory=list)


class BulkImportConfirmRequest(BaseModel):
    """Confirm and save parsed applicants to database."""
    job_id: str
    applicants: List[ParsedApplicant]
    auto_analyze: bool = False


class BulkImportConfirmResponse(BaseModel):
    """Result of saving parsed applicants."""
    imported_count: int
    proposal_ids: List[str]
    failed: List[Dict[str, str]] = Field(default_factory=list)


class ConfigUpdate(BaseModel):
    """Model for updating system configuration."""
    # AI Configuration
    ai_provider: Optional[str] = Field(None, description="AI Provider (openai, gemini, claude)")
    api_key: Optional[str] = Field(None, description="API Key for the provider")
    model_name: Optional[str] = Field(None, description="Specific model to use")
    
    # Upwork Configuration
    upwork_client_id: Optional[str] = Field(None, description="Upwork OAuth2 Client ID")
    upwork_client_secret: Optional[str] = Field(None, description="Upwork OAuth2 Client Secret")
    upwork_access_token: Optional[str] = Field(None, description="Upwork OAuth2 Access Token")
    
    # Google Sheets Configuration
    google_sheets_creds_json: Optional[str] = Field(None, description="JSON string of service account credentials")
    google_sheet_id: Optional[str] = Field(None, description="Master Google Sheet ID")
