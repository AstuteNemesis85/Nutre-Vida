from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard_service import DashboardService
from typing import Dict, Any, Optional
from datetime import date
from pydantic import BaseModel

router = APIRouter()

class GoalsRequest(BaseModel):
    calories: Optional[int] = 2000
    protein: Optional[int] = 50
    carbs: Optional[int] = 250
    fat: Optional[int] = 65
    fiber: Optional[int] = 25

@router.get("/daily/{user_id}")
def get_daily_dashboard(
    user_id: int,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get daily dashboard with intake breakdown and goal achievement"""
    try:
        dashboard_service = DashboardService(db)
        
        # Parse date if provided
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        dashboard_data = dashboard_service.get_daily_dashboard(user_id, parsed_date)
        
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="No data found for user")
        
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as e:
        print(f"Daily dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily dashboard: {str(e)}")

@router.get("/weekly/{user_id}")
def get_weekly_dashboard(
    user_id: int,
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get weekly dashboard with trends and goal achievement"""
    try:
        dashboard_service = DashboardService(db)
        
        # Parse start date if provided
        parsed_start_date = None
        if start_date:
            try:
                parsed_start_date = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        dashboard_data = dashboard_service.get_weekly_dashboard(user_id, parsed_start_date)
        
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as e:
        print(f"Weekly dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get weekly dashboard: {str(e)}")

@router.get("/monthly/{user_id}")
def get_monthly_dashboard(
    user_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get monthly dashboard with comprehensive analytics"""
    try:
        dashboard_service = DashboardService(db)
        
        # Validate month if provided
        if month and (month < 1 or month > 12):
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        dashboard_data = dashboard_service.get_monthly_dashboard(user_id, year, month)
        
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as e:
        print(f"Monthly dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monthly dashboard: {str(e)}")

@router.post("/goals/{user_id}")
def set_user_goals(
    user_id: int,
    goals: GoalsRequest,
    db: Session = Depends(get_db)
):
    """Set daily nutrition goals for a user"""
    try:
        dashboard_service = DashboardService(db)
        
        goals_dict = {
            "calories": goals.calories,
            "protein": goals.protein,
            "carbs": goals.carbs,
            "fat": goals.fat,
            "fiber": goals.fiber
        }
        
        success = dashboard_service.set_user_goals(user_id, goals_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "status": "success",
            "message": "Goals updated successfully",
            "goals": goals_dict
        }
        
    except Exception as e:
        print(f"Set goals error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set goals: {str(e)}")

@router.get("/history/{user_id}")
def get_meal_history_with_calendar(
    user_id: int,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    """Get meal history with calendar information"""
    try:
        dashboard_service = DashboardService(db)
        
        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        meal_history = dashboard_service.get_meal_history_with_calendar(user_id, days)
        
        return {
            "status": "success",
            "data": meal_history,
            "total_meals": len(meal_history)
        }
        
    except Exception as e:
        print(f"Meal history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get meal history: {str(e)}")

@router.post("/sync_meal_calendar/{meal_id}")
def sync_meal_calendar(
    meal_id: int,
    db: Session = Depends(get_db)
):
    """Manually sync meal with calendar information"""
    try:
        dashboard_service = DashboardService(db)
        
        success = dashboard_service.update_meal_calendar_info(meal_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Meal not found")
        
        return {
            "status": "success",
            "message": "Meal calendar information updated successfully"
        }
        
    except Exception as e:
        print(f"Sync meal calendar error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync meal calendar: {str(e)}")

@router.post("/update_daily_summary/{user_id}")
def update_daily_summary(
    user_id: int,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Manually update daily summary for a user"""
    try:
        dashboard_service = DashboardService(db)
        
        # Parse date if provided
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        summary_data = dashboard_service.create_or_update_daily_summary(user_id, parsed_date)
        
        if not summary_data:
            raise HTTPException(status_code=404, detail="Failed to create/update daily summary")
        
        return {
            "status": "success",
            "message": "Daily summary updated successfully",
            "data": summary_data
        }
        
    except Exception as e:
        print(f"Update daily summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update daily summary: {str(e)}")
