"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# Database URL from environment or fallback to local SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./upwork_agent.db")

# Validate DATABASE_URL - fall back to SQLite if it's a placeholder or invalid
if (not SQLALCHEMY_DATABASE_URL 
    or "your_" in SQLALCHEMY_DATABASE_URL 
    or "_here" in SQLALCHEMY_DATABASE_URL
    or "://" not in SQLALCHEMY_DATABASE_URL):
    SQLALCHEMY_DATABASE_URL = "sqlite:///./upwork_agent.db"

# Fix for some platforms (like Supabase/Heroku) returning "postgres://" instead of "postgresql://"
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine arguments based on database type
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    
    Usage:
        from backend.database import get_db
        
        db = next(get_db())
        try:
            # Use db session
            pass
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and perform auto-migration."""
    from backend.database_models import Job, Proposal  # Import models
    Base.metadata.create_all(bind=engine)
    
    # Simple migration logic for Deep Vet features
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        
        # Check proposals table columns
        if inspector.has_table("proposals"):
            columns = [c['name'] for c in inspector.get_columns('proposals')]
            
            with engine.connect() as conn:
                # Add interview_questions if missing
                if 'interview_questions' not in columns:
                    # Determine column type syntax based on dialect
                    col_type = "JSON"
                    if engine.dialect.name == 'sqlite':
                        col_type = "JSON" # SQLite supports JSON affinity in recent versions or just text
                    
                    conn.execute(text(f"ALTER TABLE proposals ADD COLUMN interview_questions {col_type}"))
                    conn.commit()
                    print("Migrated: Added interview_questions column")

                # Add chat_history if missing
                if 'chat_history' not in columns:
                    col_type = "JSON"
                    conn.execute(text(f"ALTER TABLE proposals ADD COLUMN chat_history {col_type}"))
                    conn.commit()
                    print("Migrated: Added chat_history column")
                    
    except Exception as e:
        print(f"Migration warning: {e}")
