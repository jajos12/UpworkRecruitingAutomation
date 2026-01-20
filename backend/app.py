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
    GenerateCriteriaRequest, JobCriteriaModel, ConfigUpdate
)
from backend.data_manager import DataManager
from backend.websocket_manager import ws_manager
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
from src.upwork_client import UpworkClient
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

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data manager
data_manager = DataManager()

# Initialize AI analyzer using factory pattern
try:
    from src.ai_providers.ai_analyzer_factory import create_ai_analyzer, get_available_providers
    
    ai_analyzer = create_ai_analyzer()
    
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
        result = ai_analyzer.evaluate_applicant(applicant_data, criteria, job.description)
        
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


@app.post("/api/analyze/job/{job_id}")
async def analyze_job_proposals(job_id: str, force: bool = False):
    """
    Analyze all proposals for a job.
    Set force=True to re-analyze proposals that already have scores.
    """
    if not ai_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI analyzer not available. Please set AI_PROVIDER and appropriate API key in your .env file."
        )
    
    job = data_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
    
    try:
        await ws_manager.broadcast_progress("analysis", 0.0, f"Starting analysis of {len(to_analyze)} proposals")
        
        results = []
        for i, proposal in enumerate(to_analyze):
            # Analyze
            # Note: analyze_proposal is an async endpoint function. 
            # Calling it directly avoids HTTP overhead but keeps logic in one place.
            analysis_result = await analyze_proposal(proposal.proposal_id)
            results.append(analysis_result)
            
            # Update progress
            progress = (i + 1) / len(to_analyze)
            await ws_manager.broadcast_progress(
                "analysis",
                progress,
                f"Analyzed {i + 1}/{len(to_analyze)} proposals"
            )
        
        return {
            "message": f"Analyzed {len(results)} proposals",
            "analyzed": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error analyzing job proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    if len(data_manager.get_all_jobs()) == 0:
        logger.info("Auto-seeding mock data for testing...")
        seed_mock_data(data_manager, ws_manager, ai_analyzer)
        logger.info("Mock data seeded successfully")
    
    logger.info(f"AI Analyzer: {'Available' if ai_analyzer else 'Not available'}")
    logger.info("")
    logger.info("Server started. Access the UI at: http://localhost:8000")
    logger.info("")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
