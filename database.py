"""Database configuration and models for Crib statistics."""
import os
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, func
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


class GameResult(Base):
    """Track individual game results with detailed statistics for users."""
    __tablename__ = "game_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    opponent_id = Column(String, index=True, nullable=False)
    win = Column(Boolean, nullable=False)  # True if player won, False if lost
    average_points_pegged = Column(Float, nullable=False)  # avg points per pegging round
    average_hand_score = Column(Float, nullable=False)  # avg points per hand played
    average_crib_score = Column(Float, nullable=False)  # avg crib points when dealer
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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


def record_match_result(
    user_id: Optional[str],
    opponent_id: str,
    won: bool,
    average_points_pegged: float = 0.0,
    average_hand_score: float = 0.0,
    average_crib_score: float = 0.0
) -> bool:
    """
    Record a game result for a user.
    
    Args:
        user_id: User identifier (None if not logged in)
        opponent_id: Opponent type (e.g., 'linearb', 'myrmidon')
        won: True if user won, False if lost
        average_points_pegged: Average points pegged per round
        average_hand_score: Average score per hand played
        average_crib_score: Average crib score when user was dealer
        
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
        # Create new game result record
        record = GameResult(
            user_id=user_id,
            opponent_id=opponent_id,
            win=won,
            average_points_pegged=average_points_pegged,
            average_hand_score=average_hand_score,
            average_crib_score=average_crib_score
        )
        db.add(record)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"Error recording game result: {e}")
        return False
        
    finally:
        db.close()


def get_user_stats(user_id: str) -> list:
    """
    Get game statistics for a user aggregated by opponent.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of dicts with opponent stats, or empty list if no database
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        records = db.query(GameResult).filter(
            GameResult.user_id == user_id
        ).all()
        
        # Aggregate stats by opponent
        opponent_stats = {}
        for r in records:
            opp_id = r.opponent_id
            if opp_id not in opponent_stats:
                opponent_stats[opp_id] = {
                    "opponent_id": opp_id,
                    "wins": 0,
                    "losses": 0,
                    "total_games": 0,
                    "avg_points_pegged": 0.0,
                    "avg_hand_score": 0.0,
                    "avg_crib_score": 0.0,
                }
            
            stats = opponent_stats[opp_id]
            if r.win:
                stats["wins"] += 1
            else:
                stats["losses"] += 1
            stats["total_games"] += 1
            stats["avg_points_pegged"] += r.average_points_pegged
            stats["avg_hand_score"] += r.average_hand_score
            stats["avg_crib_score"] += r.average_crib_score
        
        # Calculate averages
        for stats in opponent_stats.values():
            total = stats["total_games"]
            if total > 0:
                stats["avg_points_pegged"] /= total
                stats["avg_hand_score"] /= total
                stats["avg_crib_score"] /= total
                stats["win_rate"] = stats["wins"] / total
        
        return list(opponent_stats.values())
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return []
        
    finally:
        db.close()


def get_game_history(user_id: str, opponent_id: str = None, limit: int = 50) -> list:
    """
    Get individual game history for a user (useful for charting).
    
    Args:
        user_id: User identifier
        opponent_id: Filter by opponent type (optional)
        limit: Max number of games to return
        
    Returns:
        List of game records in chronological order
    """
    db = get_db()
    if db is None:
        return []
    
    try:
        query = db.query(GameResult).filter(GameResult.user_id == user_id)
        
        if opponent_id:
            query = query.filter(GameResult.opponent_id == opponent_id)
        
        records = query.order_by(GameResult.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "opponent_id": r.opponent_id,
                "win": r.win,
                "average_points_pegged": r.average_points_pegged,
                "average_hand_score": r.average_hand_score,
                "average_crib_score": r.average_crib_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
        
    except Exception as e:
        print(f"Error getting game history: {e}")
        return []
        
    finally:
        db.close()
