"""Database configuration and models for Crib statistics."""
import os
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()  # Load .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# Railway Postgres URLs start with postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine - only if DATABASE_URL is set
engine = None
SessionLocal = None

if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class MatchHistory(Base):
    """Track win/loss statistics for users against different opponents."""
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    opponent_id = Column(String, index=True, nullable=False)
    wins = Column(Integer, default=0, nullable=False)
    losses = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


def init_db():
    """Initialize database tables."""
    if engine:
        Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session. Returns None if no database configured."""
    if SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        return None


def record_match_result(user_id: Optional[str], opponent_id: str, won: bool) -> bool:
    """
    Record a match result for a user.
    
    Args:
        user_id: User identifier (None if not logged in)
        opponent_id: Opponent type (e.g., 'linearb', 'myrmidon')
        won: True if user won, False if lost
        
    Returns:
        True if recorded successfully, False otherwise
    """
    # Don't track if user is not logged in
    if not user_id:
        return False
    
    # Don't track if database is not configured
    db = get_db()
    if db is None:
        return False
    
    try:
        # Find or create match history record
        record = db.query(MatchHistory).filter(
            MatchHistory.user_id == user_id,
            MatchHistory.opponent_id == opponent_id
        ).first()
        
        if record:
            # Update existing record
            if won:
                record.wins += 1
            else:
                record.losses += 1
            record.updated_at = datetime.utcnow()
        else:
            # Create new record
            record = MatchHistory(
                user_id=user_id,
                opponent_id=opponent_id,
                wins=1 if won else 0,
                losses=0 if won else 1
            )
            db.add(record)
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"Error recording match result: {e}")
        return False
        
    finally:
        db.close()


def get_user_stats(user_id: str) -> list:
    """
    Get match statistics for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of dicts with opponent stats, or empty list if no database
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        records = db.query(MatchHistory).filter(
            MatchHistory.user_id == user_id
        ).all()
        
        return [
            {
                "opponent_id": r.opponent_id,
                "wins": r.wins,
                "losses": r.losses,
                "total_games": r.wins + r.losses,
                "win_rate": r.wins / (r.wins + r.losses) if (r.wins + r.losses) > 0 else 0
            }
            for r in records
        ]
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return []
        
    finally:
        db.close()
