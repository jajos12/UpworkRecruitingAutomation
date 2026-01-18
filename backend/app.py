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
    PipelineRunRequest, PipelineStatus, DaemonStatus, AnalysisResult
)
from backend.data_manager import DataManager
from backend.websocket_manager import ws_manager
from backend.mock_data import seed_mock_data
from backend import mock_data
from backend.database import init_db

# Existing codebase imports
from src.utils.logger import setup_logger
from src.utils.config_loader import ConfigLoader, AIConfig, JobCriteria
from src.ai_analyzer import AIAnalyzer

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
async def analyze_job_proposals(job_id: str):
    """Analyze all proposals for a job."""
    if not ai_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI analyzer not available. Please set ANTHROPIC_API_KEY"
        )
    
    job = data_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    proposals = data_manager.get_proposals_for_job(job_id)
    if not proposals:
        return {"message": "No proposals to analyze", "analyzed": 0}
    
    # Filter to unanalyzed proposals
    unanalyzed = [p for p in proposals if p.ai_score is None]
    if not unanalyzed:
        return {"message": "All proposals already analyzed", "analyzed": 0}
    
    try:
        await ws_manager.broadcast_progress("analysis", 0.0, f"Starting analysis of {len(unanalyzed)} proposals")
        
        results = []
        for i, proposal in enumerate(unanalyzed):
            # Analyze
            analysis_result = await analyze_proposal(proposal.proposal_id)
            results.append(analysis_result)
            
            # Update progress
            progress = (i + 1) / len(unanalyzed)
            await ws_manager.broadcast_progress(
                "analysis",
                progress,
                f"Analyzed {i + 1}/{len(unanalyzed)} proposals"
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

# Mount static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup message and seed initial data."""
    # Initialize database tables
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
