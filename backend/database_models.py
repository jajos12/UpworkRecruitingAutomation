"""SQLAlchemy ORM models for database persistence."""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base


class Job(Base):
    """Job posting table."""
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    criteria = Column(JSON, nullable=True)  # Stored as JSON
    proposal_count = Column(Integer, default=0)
    tier1_count = Column(Integer, default=0)
    tier2_count = Column(Integer, default=0)
    tier3_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to proposals
    proposals = relationship("Proposal", back_populates="job", cascade="all, delete-orphan")


class Proposal(Base):
    """Proposal table."""
    __tablename__ = "proposals"
    
    proposal_id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    
    # Freelancer profile (stored as JSON for flexibility)
    freelancer = Column(JSON, nullable=False)
    
    # Proposal details
    cover_letter = Column(Text, nullable=False)
    bid_amount = Column(Float, nullable=False)
    estimated_duration = Column(String, nullable=True)
    screening_answers = Column(Text, nullable=True)
    
    # AI analysis results
    ai_score = Column(Integer, nullable=True)
    ai_tier = Column(Integer, nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    ai_recommendation = Column(String, nullable=True)
    ai_red_flags = Column(JSON, nullable=True)  # List of strings
    ai_strengths = Column(JSON, nullable=True)  # List of strings
    
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to job
    job = relationship("Job", back_populates="proposals")
