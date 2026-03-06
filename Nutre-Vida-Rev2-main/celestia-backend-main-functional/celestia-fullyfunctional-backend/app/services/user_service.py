from sqlalchemy.orm import Session
from app.models.db_models import User, Meal
from app.models.pydantic_models import UserCreate
from typing import List, Dict, Any
from datetime import datetime
import hashlib

def get_password_hash(password: str) -> str:
    """Simple password hashing - use bcrypt in production"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(db: Session, user: UserCreate):
    """Create a new user"""
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            raise ValueError("Username already exists")
        
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username, 
            hashed_password=hashed_password, 
            profile=user.profile or {}
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise e

def get_user(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def log_meal(db: Session, user_id: int, analysis_data: Dict, portion_estimates: Dict, nutrition_summary: Dict, recommendations: Dict):
    """Log a meal for a user with automatic calendar sync and notification tracking"""
    try:
        now = datetime.now()
        
        meal = Meal(
            user_id=user_id,
            analysis_data=analysis_data or {},
            portion_estimates=portion_estimates or {},
            nutrition_summary=nutrition_summary or {},
            recommendations=recommendations or {},
            upload_date=now.date(),
            upload_time=now,
            day_of_week=now.strftime("%A")  # Monday, Tuesday, etc.
        )
        db.add(meal)
        
        # Update user's last meal time for reminder tracking
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_meal_time = now
        
        db.commit()
        db.refresh(meal)
        
        # Update daily summary after logging meal
        try:
            from app.services.dashboard_service import DashboardService
            dashboard_service = DashboardService(db)
            dashboard_service.create_or_update_daily_summary(user_id, now.date())
        except Exception as dashboard_error:
            print(f"Failed to update daily summary: {dashboard_error}")
            # Don't fail the meal logging if dashboard update fails
        
        return meal
    except Exception as e:
        db.rollback()
        print(f"Failed to log meal: {e}")
        raise e

def get_meal_history(db: Session, user_id: int) -> List[Meal]:
    """Get meal history for a user"""
    try:
        return db.query(Meal).filter(Meal.user_id == user_id).order_by(Meal.id.desc()).limit(20).all()
    except Exception as e:
        print(f"Failed to get meal history: {e}")
        return []
