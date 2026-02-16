"""
FastAPI backend for Upwork Recruitment Agent.

Main web server providing REST API and WebSocket endpoints.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.encoders import jsonable_encoder
from typing import List, Optional
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Backend imports
from backend.models import (
    JobCreate, JobResponse, ProposalCreate, ProposalResponse,
    PipelineRunRequest, PipelineStatus, DaemonStatus, AnalysisResult,
    GenerateCriteriaRequest, JobCriteriaModel, ConfigUpdate,
    InterviewGuide, InterviewQuestion, InterviewGenerationConfig,
    ChatRequest, ChatMessage, LoginRequest,
    BulkImportRequest, ParsedApplicant, BulkImportParseResponse,
    BulkImportConfirmRequest, BulkImportConfirmResponse,
    FreelancerProfile
)
from backend.data_manager import DataManager
from backend.websocket_manager import ws_manager
from backend.auth import auth_manager, get_current_user
from backend.mock_data import seed_mock_data
from backend import mock_data
from backend.database import init_db

# Existing codebase imports
from src.utils.logger import setup_logger
from src.utils.config_loader import (
    ConfigLoader, AIConfig, JobCriteria, UpworkConfig, 
    GoogleSheetsConfig, CommunicationConfig, NotificationConfig
)
from src.ai_analyzer import AIAnalyzer
from src.pipeline import Pipeline
from src.upwork_client import UpworkClient, MockUpworkClient
from src.sheets_manager import SheetsManager
from src.communicator import Communicator

from fastapi import BackgroundTasks
import threading

# Initialize logger
logger = setup_logger("backend", level="INFO")

# Initialize FastAPI app
app = FastAPI(
    title="Upwork Recruitment Agent API",
    description="REST API for AI-powered Upwork recruitment automation",
    version="1.0.0"
)

# GZip compression for API responses (min 500 bytes)
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple stats cache (avoids re-querying DB on every page load)
import time as _time
_stats_cache = {"data": None, "ts": 0}
_STATS_TTL = 5  # seconds

# Initialize data manager
data_manager = DataManager()

# Initialize AI analyzer using factory pattern
try:
    from src.ai_providers.ai_analyzer_factory import create_ai_analyzer, get_available_providers
    
    # Check for MOCK_MODE override for AI
    provider_override = None
    if os.getenv("MOCK_MODE", "false").lower() == "true":
        provider_override = "mock"
        logger.info("[INFO] MOCK_MODE enabled, using Mock AI Analyzer")
    
    ai_analyzer = create_ai_analyzer(provider=provider_override)
    
    if ai_analyzer:
        logger.info("[SUCCESS] AI Analyzer initialized")
        providers = get_available_providers()
        logger.info(f"[INFO] Available providers: {', '.join(providers) if providers else 'none'}")
    else:
        logger.warning("[WARNING] No AI provider configured - AI analysis will be unavailable")
        logger.info("[INFO] Set AI_PROVIDER and corresponding API key in .env (openai, claude, gemini)")
        
except Exception as e:
    ai_analyzer = None
    logger.warning(f"[ERROR] Could not initialize AI analyzer: {e}")

# Pipeline status
pipeline_status = PipelineStatus(running=False)
daemon_status = DaemonStatus(running=False)


# ============================================================================
# Auth endpoints
# ============================================================================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    Uses Supabase Auth backend.
    """
    result = auth_manager.login(request.email, request.password)
    return result

@app.post("/api/auth/signup")
async def signup(request: LoginRequest):
    """
    Create a new user.
    """
    result = auth_manager.signup(request.email, request.password)
    return result



# ============================================================================
# Root & Health
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - serve frontend."""
    return FileResponse("frontend/index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

def run_pipeline_task(request: PipelineRunRequest):
    """Background task to run the pipeline."""
    global pipeline_status
    
    pipeline_status.running = True
    pipeline_status.current_phase = "initializing"
    pipeline_status.message = "Initializing pipeline components..."
    
    try:
        # Construct Configs from Env
        upwork_conf = UpworkConfig(
            client_id=os.getenv("UPWORK_CLIENT_ID", ""),
            client_secret=os.getenv("UPWORK_CLIENT_SECRET", ""),
            access_token=os.getenv("UPWORK_ACCESS_TOKEN", ""), 
            refresh_token=os.getenv("UPWORK_REFRESH_TOKEN", "")
        )
        
        # Check if secrets file exists
        sheets_creds = "secrets/gcp_service_account.json"
        
        sheets_conf = GoogleSheetsConfig(
            credentials_path=sheets_creds,
            spreadsheet_id=os.getenv("GOOGLE_SHEET_ID", "")
        )
        
        comm_conf = CommunicationConfig(
            auto_respond_tier1=True,
            follow_up_after_hours=48,
            batch_decline_tier3=True
        )
        
        # Initialize Components
        
        # Upwork
        try:
             mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
             if mock_mode:
                 upwork_client = MockUpworkClient(upwork_conf)
                 logger.warning("USING MOCK UPWORK CLIENT")
             else:
                 upwork_client = UpworkClient(upwork_conf)
        except Exception as e:
             logger.error(f"Failed to init UpworkClient: {e}")
             if request.fetch:
                 raise Exception("Upwork Client failed to initialize. Check credentials.")
             upwork_client = None

        # Sheets
        try:
             sheets_manager = SheetsManager(sheets_conf)
        except Exception as e:
             logger.error(f"Failed to init SheetsManager: {e}")
             sheets_manager = None
             
        # Communicator
        try:
             loader = ConfigLoader() 
             communicator = Communicator(
                 upwork_client=upwork_client,
                 sheets_manager=sheets_manager,
                 config=comm_conf,
                 ai_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                 config_loader=loader
             )
        except Exception as e:
             logger.error(f"Failed to init Communicator: {e}")
             communicator = None

        if not ai_analyzer:
            # We can still run extraction even if AI is down
            if request.analyze:
                raise Exception("AI Analyzer not initialized.")

        # Initialize Pipeline
        pipeline = Pipeline(
            upwork_client=upwork_client,
            ai_analyzer=ai_analyzer,
            sheets_manager=sheets_manager,
            communicator=communicator,
            config_loader=ConfigLoader()
        )
        
        pipeline_status.current_phase = "running"
        pipeline_status.message = "Pipeline running..."
        
        # Run
        # Note: pipeline.run_full_pipeline is synchronous and blocking
        results = pipeline.run_full_pipeline(
            fetch=request.fetch,
            analyze=request.analyze,
            communicate=request.communicate,
            dry_run=request.dry_run
        )
        
        pipeline_status.stats = results
        pipeline_status.message = "Pipeline completed successfully"
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        pipeline_status.message = f"Error: {str(e)}"
    finally:
        pipeline_status.running = False
        pipeline_status.current_phase = "idle"


@app.post("/api/pipeline/run")
async def run_pipeline(request: PipelineRunRequest, background_tasks: BackgroundTasks):
    """Trigger the full recruitment pipeline."""
    if pipeline_status.running:
        raise HTTPException(status_code=400, detail="Pipeline is already running")
        
    background_tasks.add_task(run_pipeline_task, request)
    
    return {"message": "Pipeline started", "status": "running"}

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get current pipeline status."""
    return pipeline_status

def update_env_file(key: str, value: str):
    """Updates or adds a key-value pair in the .env file."""
    env_path = Path(".env")
    if not env_path.exists():
        env_path.touch()

    try:
        content = env_path.read_text()
        lines = content.splitlines()
    except Exception:
        lines = []

    new_lines = []
    found = False
    
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append(f"{key}={value}")
    
    # Ensure newline at end if not empty, join with newlines
    output = "\n".join(new_lines)
    env_path.write_text(output)


@app.post("/api/analyze/interview/{proposal_id}", response_model=InterviewGuide)
async def generate_interview_guide(proposal_id: str, config: Optional[InterviewGenerationConfig] = None):
    """Generate an interview guide for a candidate."""
    if not ai_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI analyzer not available. Please configuration AI provider."
        )
    
    proposal = data_manager.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Check for existing questions if no new config meant to regenerate
    if not config and proposal.interview_questions:
        return InterviewGuide(proposal_id=proposal_id, questions=proposal.interview_questions)
        
    job = data_manager.get_job(proposal.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get data
    applicant_data = {
        "applicant_id": proposal.freelancer.freelancer_id,
        "applicant_name": proposal.freelancer.name,
        "profile_title": proposal.freelancer.title,
        "hourly_rate_profile": proposal.freelancer.hourly_rate,
        "skills": proposal.freelancer.skills,
        "bio": proposal.freelancer.bio,
        "certifications": proposal.freelancer.certifications,
        "portfolio_items": proposal.freelancer.portfolio_items,
        "work_history_summary": proposal.freelancer.work_history_summary,
        "cover_letter": proposal.cover_letter,
        "applicant_profile": proposal.freelancer.dict()
    }
    
    try:
        # Generate questions
        questions_raw = ai_analyzer.generate_interview_questions(
            applicant_data, 
            job.description, 
            config=config.dict() if config else None
        )
        
        # Convert to Pydantic models
        questions = []
        for q in questions_raw:
            # Handle list answers (AI sometimes returns lists)
            expected_answer = q.get("expected_answer")
            if isinstance(expected_answer, list):
                expected_answer = "; ".join(expected_answer)
            elif expected_answer is not None:
                expected_answer = str(expected_answer)

            # Handle list contexts
            context = q.get("context")
            if isinstance(context, list):
                context = "; ".join(context)
            elif context is not None:
                context = str(context)

            questions.append(InterviewQuestion(
                type=q.get("type", "General"),
                question=q.get("question", ""),
                context=context,
                expected_answer=expected_answer
            ))
        
        # Save to DB
        data_manager.update_proposal_interview_questions(proposal_id, questions)
            
        return InterviewGuide(proposal_id=proposal_id, questions=questions)
        
    except Exception as e:
        logger.error(f"Error generating interview guide: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/chat/{proposal_id}", response_model=ChatMessage)
async def chat_with_candidate(proposal_id: str, request: ChatRequest):
    """Chat with a candidate (The Investigator)."""
    if not ai_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI analyzer not available."
        )
    
    proposal = data_manager.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    job = data_manager.get_job(proposal.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get data
    applicant_data = {
        "applicant_name": proposal.freelancer.name,
        "profile_title": proposal.freelancer.title,
        "skills": proposal.freelancer.skills,
        "bio": proposal.freelancer.bio,
        "cover_letter": proposal.cover_letter,
        "work_history_summary": proposal.freelancer.work_history_summary,
        "certifications": proposal.freelancer.certifications,
        "portfolio_items": proposal.freelancer.portfolio_items
    }
    
    # Get existing history
    history = []
    if hasattr(proposal, "chat_history") and proposal.chat_history:
        history = proposal.chat_history # This should be List[ChatMessage] or List[Dict]

    # Prepare context for AI (clean list of role/content)
    ai_context = []
    for h in history:
        if isinstance(h, dict):
            ai_context.append({"role": h.get("role"), "content": h.get("content")})
        else:
            ai_context.append({"role": h.role, "content": h.content})

    try:
        # Get AI Response
        response_text = ai_analyzer.chat_with_candidate(
            request.message,
            applicant_data,
            job.description,
            ai_context
        )
        
        # Create message objects
        user_msg = ChatMessage(role="user", content=request.message, timestamp=datetime.utcnow())
        ai_msg = ChatMessage(role="assistant", content=response_text, timestamp=datetime.utcnow())
        
        # Update history (Full history + new messages)
        # We need to append to the original 'history' list but ensure uniform types
        # 'history' might contain dicts (from DB direct access) or objects (from Pydantic)
        
        updated_history = []
        # Add old messages
        if history:
            updated_history.extend(history)
            
        # Add new messages
        updated_history.extend([user_msg, ai_msg])

        # Serialize everything to JSON-compatible format (handling datetimes)
        serialized_history = jsonable_encoder(updated_history)
        
        data_manager.update_proposal_chat_history(proposal_id, serialized_history)
        
        return ai_msg
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """Get current system configuration."""
    # Check for GCP credentials file
    gcp_creds_path = Path("secrets/gcp_service_account.json")
    has_gcp_creds = gcp_creds_path.exists()

    return {
        # AI Config
        "ai_provider": os.getenv("AI_PROVIDER", "openai"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest"),
        "claude_model": os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_gemini_key": bool(os.getenv("GEMINI_API_KEY")),
        "has_claude_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        
        # Upwork Config
        "has_upwork_client_id": bool(os.getenv("UPWORK_CLIENT_ID")),
        "has_upwork_secret": bool(os.getenv("UPWORK_CLIENT_SECRET")),
        "has_upwork_token": bool(os.getenv("UPWORK_ACCESS_TOKEN")),
        
        # Google Sheets Config
        "google_sheet_id": os.getenv("GOOGLE_SHEET_ID", ""),
        "has_google_creds": has_gcp_creds
    }

@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update system configuration."""
    global ai_analyzer
    
    # 1. AI Configuration
    if config.ai_provider:
        os.environ["AI_PROVIDER"] = config.ai_provider
        update_env_file("AI_PROVIDER", config.ai_provider)
    
    # Update AI API Key
    if config.api_key and config.ai_provider:
        key_name = ""
        if config.ai_provider == "openai":
            key_name = "OPENAI_API_KEY"
        elif config.ai_provider == "gemini":
            key_name = "GEMINI_API_KEY"
        elif config.ai_provider == "claude":
            key_name = "ANTHROPIC_API_KEY"
            
        if key_name:
            os.environ[key_name] = config.api_key
            update_env_file(key_name, config.api_key)
            
    # Update AI Model
    if config.model_name and config.ai_provider:
        model_env_key = ""
        if config.ai_provider == "openai":
            model_env_key = "OPENAI_MODEL"
        elif config.ai_provider == "gemini":
            model_env_key = "GEMINI_MODEL"
        elif config.ai_provider == "claude":
            model_env_key = "CLAUDE_MODEL"
            
        if model_env_key:
             os.environ[model_env_key] = config.model_name
             update_env_file(model_env_key, config.model_name)

    # 2. Upwork Configuration
    if config.upwork_client_id:
        os.environ["UPWORK_CLIENT_ID"] = config.upwork_client_id
        update_env_file("UPWORK_CLIENT_ID", config.upwork_client_id)
        
    if config.upwork_client_secret:
        os.environ["UPWORK_CLIENT_SECRET"] = config.upwork_client_secret
        update_env_file("UPWORK_CLIENT_SECRET", config.upwork_client_secret)

    if config.upwork_access_token:
        os.environ["UPWORK_ACCESS_TOKEN"] = config.upwork_access_token
        update_env_file("UPWORK_ACCESS_TOKEN", config.upwork_access_token)

    # 3. Google Sheets Configuration
    if config.google_sheet_id:
        os.environ["GOOGLE_SHEET_ID"] = config.google_sheet_id
        update_env_file("GOOGLE_SHEET_ID", config.google_sheet_id)
        
    if config.google_sheets_creds_json:
        try:
            secrets_dir = Path("secrets")
            secrets_dir.mkdir(exist_ok=True)
            creds_path = secrets_dir / "gcp_service_account.json"
            creds_path.write_text(config.google_sheets_creds_json)
        except Exception as e:
            logger.error(f"Failed to save GCP credentials: {e}")
            raise HTTPException(status_code=500, detail="Failed to save Google Credentials")

    # Re-initialize AI Analyzer if AI settings changed
    if config.ai_provider or config.api_key or config.model_name:
        try:
            from src.ai_providers.ai_analyzer_factory import create_ai_analyzer
            new_analyzer = create_ai_analyzer()
            if new_analyzer:
                ai_analyzer = new_analyzer
                logger.info(f"AI Analyzer re-initialized with provider: {config.ai_provider}")
                return {"status": "success", "message": "Configuration updated and AI re-initialized"}
            else:
                logger.error("Failed to re-initialize AI analyzer")
                # Don't fail the whole request if just AI failed, since we might have updated Upwork keys
                return {"status": "warning", "message": "Settings saved, but AI initialization failed. Check API key."}
        except Exception as e:
            logger.error(f"Error re-initializing AI analyzer: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    return {"status": "success", "message": "Configuration saved"}

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_available": ai_analyzer is not None
    }


# ============================================================================
# Stats Endpoint
# ============================================================================

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics with caching."""
    now = _time.time()
    if _stats_cache["data"] is None or (now - _stats_cache["ts"]) > _STATS_TTL:
        _stats_cache["data"] = data_manager.get_stats()
        _stats_cache["ts"] = now
    return _stats_cache["data"]


# ============================================================================
# Job Endpoints
# ============================================================================

@app.post("/api/jobs", response_model=JobResponse, status_code=201)
async def create_job(job: JobCreate):
    """Create a new job posting."""
    try:
        new_job = data_manager.create_job(job)
        
        # Broadcast activity
        await ws_manager.broadcast_activity(
            "job_created",
            f"Created job: {job.title}",
            {"job_id": new_job.job_id}
        )
        
        # Update stats
        await ws_manager.broadcast_stats(data_manager.get_stats())
        
        return new_job
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs():
    """Get all job postings."""
    return data_manager.get_all_jobs()


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get a specific job by ID."""
    job = data_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/api/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, job: JobCreate):
    """
    Update a job and its criteria.
    Use this when editing auto-generated criteria.
    """
    updated_job = data_manager.update_job(job_id, job)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await ws_manager.broadcast_activity(
        "job_updated",
        f"Updated job: {updated_job.title}",
        {"job_id": job_id}
    )
    
    return updated_job


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and all its proposals."""
    success = data_manager.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await ws_manager.broadcast_activity(
        "job_deleted",
        f"Deleted job: {job_id}"
    )
    await ws_manager.broadcast_stats(data_manager.get_stats())
    
    return {"message": "Job deleted successfully"}


@app.post("/api/jobs/generate-criteria", response_model=JobCriteriaModel)
async def generate_job_criteria(request: GenerateCriteriaRequest):
    """
    Generate hiring criteria from a job description using AI.
    """
    if not ai_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI analyzer not available. Please configure AI_PROVIDER in .env"
        )
    
    try:
        criteria_dict = ai_analyzer.generate_criteria(request.description)
        return JobCriteriaModel(**criteria_dict)
    except Exception as e:
        logger.error(f"Error generating criteria: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Proposal Endpoints
# ============================================================================

@app.post("/api/proposals", response_model=ProposalResponse, status_code=201)
async def create_proposal(proposal: ProposalCreate):
    """Create a new proposal."""
    # Check if job exists
    job = data_manager.get_job(proposal.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        new_proposal = data_manager.create_proposal(proposal)
        
        # Broadcast activity
        await ws_manager.broadcast_activity(
            "proposal_created",
            f"New proposal from {proposal.freelancer.name}",
            {"proposal_id": new_proposal.proposal_id, "job_id": proposal.job_id}
        )
        
        # Update stats
        await ws_manager.broadcast_stats(data_manager.get_stats())
        
        return new_proposal
    except Exception as e:
        logger.error(f"Error creating proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposals", response_model=List[ProposalResponse])
async def get_proposals(job_id: Optional[str] = None):
    """Get all proposals, optionally filtered by job."""
    if job_id:
        return data_manager.get_proposals_for_job(job_id)
    return data_manager.get_all_proposals()


@app.get("/api/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(proposal_id: str):
    """Get a specific proposal by ID."""
    proposal = data_manager.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@app.delete("/api/proposals/{proposal_id}")
async def delete_proposal(proposal_id: str):
    """Delete a proposal."""
    success = data_manager.delete_proposal(proposal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    await ws_manager.broadcast_activity(
        "proposal_deleted",
        f"Deleted proposal: {proposal_id}"
    )
    await ws_manager.broadcast_stats(data_manager.get_stats())
    
    return {"message": "Proposal deleted successfully"}


@app.patch("/api/proposals/{proposal_id}/status")
async def update_proposal_status(proposal_id: str, status_data: dict):
    """Update proposal status (manual override)."""
    success = data_manager.update_proposal_status(proposal_id, status_data.get("status"))
    if not success:
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    await ws_manager.broadcast_activity(
        "status_updated",
        f"Updated proposal {proposal_id} status to {status_data.get('status')}"
    )
    return {"message": "Status updated"}


# ============================================================================
# Analysis Endpoints
# ============================================================================

@app.post("/api/analyze/{proposal_id}")
async def analyze_proposal(proposal_id: str):
    """Analyze a single proposal with AI."""
    if not ai_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI analyzer not available. Please set AI_PROVIDER and appropriate API key in your .env file."
        )
    
    proposal = data_manager.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    job = data_manager.get_job(proposal.job_id)
    if not job or not job.criteria:
        raise HTTPException(status_code=400, detail="Job criteria not defined")
    
    try:
        # Convert to format expected by AI analyzer
        applicant_data = {
            "applicant_id": proposal.freelancer.freelancer_id,
            "applicant_name": proposal.freelancer.name,
            "profile_title": proposal.freelancer.title,
            "hourly_rate_profile": proposal.freelancer.hourly_rate,
            "job_success_score": proposal.freelancer.job_success_score,
            "total_earnings": proposal.freelancer.total_earnings,
            "top_rated_status": proposal.freelancer.top_rated_status,
            "skills": proposal.freelancer.skills,
            "bio": proposal.freelancer.bio,
            "certifications": proposal.freelancer.certifications,
            "portfolio_items": proposal.freelancer.portfolio_items,
            "work_history_summary": proposal.freelancer.work_history_summary,
            "cover_letter": proposal.cover_letter,
            "bid_amount": proposal.bid_amount,
            "screening_answers": proposal.screening_answers,
        }
        
        # Convert criteria
        criteria = JobCriteria(
            job_id=job.job_id,
            job_title=job.title,
            must_have=job.criteria.must_have,
            nice_to_have=job.criteria.nice_to_have,
            red_flags=job.criteria.red_flags
        )
        
        # Broadcast start
        await ws_manager.broadcast_activity(
            "analysis_started",
            f"Analyzing proposal from {proposal.freelancer.name}",
            {"proposal_id": proposal_id}
        )
        
        # Run analysis
        result = await asyncio.to_thread(ai_analyzer.evaluate_applicant, applicant_data, criteria, job.description)
        
        # Create analysis result
        analysis = AnalysisResult(
            proposal_id=proposal_id,
            score=result["score"],
            tier=result["tier"],
            reasoning=result["reasoning"],
            recommendation=result["recommendation"],
            red_flags=result.get("red_flags", []),
            strengths=result.get("strengths", [])
        )
        
        # Update proposal
        data_manager.update_proposal_analysis(proposal_id, analysis)
        
        # Broadcast completion
        await ws_manager.broadcast_activity(
            "analysis_complete",
            f"Analyzed {proposal.freelancer.name}: Tier {analysis.tier}, Score {analysis.score}",
            {"proposal_id": proposal_id, "tier": analysis.tier, "score": analysis.score}
        )
        
        # Update stats
        await ws_manager.broadcast_stats(data_manager.get_stats())
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing proposal: {e}")
        await ws_manager.broadcast_error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/analyze/job/{job_id}", status_code=202)
async def analyze_job_proposals(job_id: str, force: bool = False, background_tasks: BackgroundTasks = None):
    """
    Analyze all proposals for a job in the background.
    Set force=True to re-analyze proposals that already have scores.
    """
    proposals = data_manager.get_proposals_for_job(job_id)
    if not proposals:
        return {"message": "No proposals to analyze", "analyzed": 0}
    
    # Filter proposals
    if force:
        to_analyze = proposals
    else:
        to_analyze = [p for p in proposals if p.ai_score is None]
        
    if not to_analyze:
        return {"message": "All proposals already analyzed", "analyzed": 0}

    # Define background task
    async def _analyze_batch(proposals_to_process: List[ProposalResponse]):
        if not ai_analyzer:
             logger.error("AI analyzer not available for batch processing")
             return

        await ws_manager.broadcast_progress("analysis", 0.0, f"Starting analysis of {len(proposals_to_process)} proposals")
        
        results = []
        for i, proposal in enumerate(proposals_to_process):
            try:
                # Use semaphore or rate limiter if needed inside ai_analyzer
                analysis_result = await analyze_proposal(proposal.proposal_id)
                results.append(analysis_result)
            except Exception as e:
                logger.error(f"Failed to analyze proposal {proposal.proposal_id}: {e}")
            
            # Update progress
            progress = (i + 1) / len(proposals_to_process)
            await ws_manager.broadcast_progress(
                "analysis",
                progress,
                f"Analyzed {i + 1}/{len(proposals_to_process)} proposals"
            )

    # Add to background tasks
    if background_tasks:
        background_tasks.add_task(_analyze_batch, to_analyze)
    else:
         # Fallback if no background_tasks provided (shouldn't happen with FastAPI)
         asyncio.create_task(_analyze_batch(to_analyze))
        
    return {
        "message": f"Analysis started for {len(to_analyze)} proposals",
        "status": "processing",
        "analyzed": len(to_analyze) # Expected count
    }


# ============================================================================
# Bulk Import Endpoints
# ============================================================================

@app.post("/api/import/parse", response_model=BulkImportParseResponse)
async def parse_raw_import(request: BulkImportRequest):
    """
    Parse raw text into structured applicant profiles using AI.
    Returns parsed data for review - does NOT save to database.
    """
    if not ai_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI analyzer not available. Please configure an AI provider in Settings."
        )

    # Verify job exists
    job = data_manager.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        # Call AI to parse raw text
        result = await asyncio.to_thread(
            ai_analyzer.parse_raw_applicants,
            request.raw_text,
            job.description,
            request.input_format_hint
        )

        raw_applicants = result.get("applicants", [])
        warnings = result.get("warnings", [])

        # Convert raw AI output to ParsedApplicant models
        parsed_applicants = []
        for i, raw in enumerate(raw_applicants):
            try:
                # Use `or` fallbacks — dict.get("key", default) won't work
                # when the AI explicitly returns None for a key
                freelancer = FreelancerProfile(
                    freelancer_id=raw.get("freelancer_id") or f"import-{i+1}",
                    name=raw.get("name") or f"Unknown Applicant #{i+1}",
                    title=raw.get("title") or "Freelancer",
                    hourly_rate=raw.get("hourly_rate"),
                    job_success_score=raw.get("job_success_score"),
                    total_earnings=raw.get("total_earnings"),
                    top_rated_status=raw.get("top_rated_status"),
                    skills=raw.get("skills") or [],
                    bio=raw.get("bio") or "",
                    certifications=raw.get("certifications") or [],
                    portfolio_items=raw.get("portfolio_items") or [],
                    work_history_summary=raw.get("work_history_summary"),
                    profile_url=raw.get("profile_url")
                )

                parsed_applicants.append(ParsedApplicant(
                    freelancer=freelancer,
                    cover_letter=raw.get("cover_letter") or "",
                    bid_amount=float(raw.get("bid_amount") or 0),
                    estimated_duration=raw.get("estimated_duration"),
                    screening_answers=raw.get("screening_answers"),
                    confidence=float(raw.get("confidence") or 0.5),
                    parse_notes=raw.get("parse_notes") or []
                ))
            except Exception as e:
                warnings.append(f"Failed to parse applicant #{i+1}: {str(e)}")
                logger.warning(f"Failed to parse applicant #{i+1}: {e}")

        # If the AI "found" applicants but ALL of them failed validation,
        # that strongly suggests the input wasn't real applicant data
        if len(raw_applicants) > 0 and len(parsed_applicants) == 0:
            raise HTTPException(
                status_code=422,
                detail="The uploaded data doesn't appear to contain valid applicant profiles. "
                       "Please make sure you're uploading files with applicant information "
                       "(names, skills, cover letters, etc.)."
            )

        return BulkImportParseResponse(
            applicants=parsed_applicants,
            total_found=len(parsed_applicants),
            parse_warnings=warnings
        )

    except Exception as e:
        logger.error(f"Error parsing raw import data: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


@app.post("/api/import/confirm", response_model=BulkImportConfirmResponse)
async def confirm_import(request: BulkImportConfirmRequest, background_tasks: BackgroundTasks):
    """
    Save reviewed/edited applicants as proposals in the database.
    Optionally triggers batch AI analysis after import.
    """
    # Verify job exists
    job = data_manager.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    imported_ids = []
    failed = []

    for applicant in request.applicants:
        try:
            proposal_data = ProposalCreate(
                job_id=request.job_id,
                freelancer=applicant.freelancer,
                cover_letter=applicant.cover_letter if len(applicant.cover_letter) >= 10 else "No cover letter provided (imported via bulk import)",
                bid_amount=applicant.bid_amount if applicant.bid_amount > 0 else 0.01,
                estimated_duration=applicant.estimated_duration,
                screening_answers=applicant.screening_answers
            )

            new_proposal = data_manager.create_proposal(proposal_data)
            imported_ids.append(new_proposal.proposal_id)

            # Broadcast activity
            await ws_manager.broadcast_activity(
                "proposal_imported",
                f"Imported {applicant.freelancer.name} via bulk import",
                {"proposal_id": new_proposal.proposal_id, "job_id": request.job_id}
            )

        except Exception as e:
            logger.error(f"Failed to import {applicant.freelancer.name}: {e}")
            failed.append({"name": applicant.freelancer.name, "error": str(e)})

    # Update stats
    await ws_manager.broadcast_stats(data_manager.get_stats())

    await ws_manager.broadcast_activity(
        "bulk_import_complete",
        f"Bulk import complete: {len(imported_ids)} imported, {len(failed)} failed",
        {"job_id": request.job_id, "count": len(imported_ids)}
    )

    # Optionally trigger batch analysis
    if request.auto_analyze and imported_ids and ai_analyzer:
        background_tasks.add_task(_run_batch_analysis, request.job_id)

    return BulkImportConfirmResponse(
        imported_count=len(imported_ids),
        proposal_ids=imported_ids,
        failed=failed
    )


async def _run_batch_analysis(job_id: str):
    """Helper to run batch analysis after import."""
    try:
        proposals = data_manager.get_proposals_for_job(job_id)
        to_analyze = [p for p in proposals if p.ai_score is None]

        for i, proposal in enumerate(to_analyze):
            try:
                await analyze_proposal(proposal.proposal_id)
            except Exception as e:
                logger.error(f"Batch analysis failed for {proposal.proposal_id}: {e}")

            progress = (i + 1) / len(to_analyze)
            await ws_manager.broadcast_progress(
                "analysis", progress,
                f"Analyzed {i + 1}/{len(to_analyze)} imported proposals"
            )
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")


# ============================================================================
# Statistics & Dashboard
# ============================================================================

@app.get("/api/stats")
async def get_stats():
    """Get overall statistics."""
    return data_manager.get_stats()


# ============================================================================
# AI Configuration Endpoints
# ============================================================================

@app.get("/api/ai/providers")
async def get_ai_providers():
    """Get list of available and supported AI providers."""
    return {
        "available": get_available_providers(),
        "current": os.getenv("AI_PROVIDER", "claude"),
        "current_model": os.getenv("AI_MODEL", "default")
    }


@app.post("/api/ai/switch")
async def switch_ai_provider(config: dict):
    """
    Switch the active AI provider at runtime.
    
    Expected body: {"provider": "openai", "model": "gpt-4o-mini"}
    """
    global ai_analyzer
    
    provider = config.get("provider")
    model = config.get("model")
    
    if not provider:
        raise HTTPException(status_code=400, detail="Provider is required")
    
    logger.info(f"Switching AI provider to: {provider} (model: {model or 'default'})")
    
    new_analyzer = create_ai_analyzer(provider=provider, model=model)
    
    if new_analyzer:
        ai_analyzer = new_analyzer
        # Update env vars for persistence if restarted (though .env file is better)
        os.environ["AI_PROVIDER"] = provider
        if model:
            os.environ["AI_MODEL"] = model
            
        return {
            "status": "success",
            "message": f"Successfully switched to {provider}",
            "provider": provider,
            "model": model or "default"
        }
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to switch to {provider}. Check if API key is set."
        )


# ============================================================================
# Mock Data Endpoints
# ============================================================================

@app.post("/api/seed-data")
async def seed_mock_data_endpoint():
    """Seed database with mock data for testing."""
    try:
        # Clear existing data
        data_manager.clear_all_data()
        
        # Generate jobs
        jobs = mock_data.generate_mock_jobs(3)
        created_jobs = []
        
        for i, job in enumerate(jobs):
            created_job = data_manager.create_job(job)
            created_jobs.append(created_job)
            
            # Generate proposals for each job
            proposals = mock_data.generate_realistic_proposal_mix(
                created_job.job_id,
                created_job.title
            )
            
            for proposal in proposals:
                data_manager.create_proposal(proposal)
        
        # Broadcast activity
        await ws_manager.broadcast_activity(
            "data_seeded",
            f"Seeded {len(created_jobs)} jobs with mock proposals"
        )
        await ws_manager.broadcast_stats(data_manager.get_stats())
        
        stats = data_manager.get_stats()
        return {
            "message": "Mock data seeded successfully",
            "jobs_created": len(created_jobs),
            "proposals_created": stats["total_proposals"]
        }
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear-data")
async def clear_data():
    """Clear all data."""
    data_manager.clear_all_data()
    
    await ws_manager.broadcast_activity("data_cleared", "All data cleared")
    await ws_manager.broadcast_stats(data_manager.get_stats())
    
    return {"message": "All data cleared"}


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ============================================================================
# Static Files (Frontend)
# ============================================================================

# Mount static files if directory exists
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
else:
    logger.warning("Frontend directory not found. Static files will not be served.")


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup message and seed initial data."""
    # Initialize database tables
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # We don't raise here to allow the container to start and be debuggable
        # In production, you might want to fail hard if DB is critical
    
    logger.info("UpworkRecruitmentAgent Web UI Server Started")
    logger.info("Dashboard available at http://localhost:8000")
    logger.info("API docs available at http://localhost:8000/docs")
    
    # Auto-seed mock data if starting with empty database
    try:
        if len(data_manager.get_all_jobs()) == 0:
            logger.info("Auto-seeding mock data for testing...")
            seed_mock_data(data_manager, ws_manager, ai_analyzer)
            logger.info("Mock data seeded successfully")
    except Exception as e:
        logger.warning(f"Could not auto-seed data (DB may be unavailable): {e}")
    
    logger.info(f"AI Analyzer: {'Available' if ai_analyzer else 'Not available'}")
    logger.info("")
    logger.info("Server started. Access the UI at: http://localhost:8000")
    logger.info("")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)