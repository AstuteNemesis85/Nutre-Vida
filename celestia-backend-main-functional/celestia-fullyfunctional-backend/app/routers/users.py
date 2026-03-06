from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.user_service import create_user, get_user, get_meal_history, log_meal
from app.models.pydantic_models import UserCreate, User, MealLog
from app.models.google_models import GoogleUserCreate
from app.models.db_models import User as DBUser
from typing import Dict, Any, List

router = APIRouter()

@router.post("/", response_model=User)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = create_user(db, user)
        return db_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"User creation failed: {str(e)}")

@router.post("/google", response_model=User)
def create_or_login_google_user(user_data: GoogleUserCreate, db: Session = Depends(get_db)):
    try:
        print(f"Received Google user data: {user_data}")
        
        # Validate required fields
        if not user_data.google_id or not user_data.email:
            raise HTTPException(status_code=400, detail="Missing required fields: google_id and email")
        
        # Check if user exists
        db_user = db.query(DBUser).filter(DBUser.google_id == user_data.google_id).first()
        
        if db_user:
            # Update user info
            db_user.name = user_data.name or db_user.name
            db_user.email = user_data.email or db_user.email
            db_user.picture = user_data.picture or db_user.picture
            print(f"Updated existing user: {db_user.id}")
        else:
            # Create new user
            db_user = DBUser(
                google_id=user_data.google_id,
                email=user_data.email,
                name=user_data.name or "Unknown User",
                picture=user_data.picture,
                profile={},
                daily_goals={}
            )
            db.add(db_user)
            print(f"Created new user for Google ID: {user_data.google_id}")
        
        db.commit()
        db.refresh(db_user)
        print(f"Successfully processed user: {db_user.id}")
        return db_user
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Google authentication error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/meals", response_model=List[MealLog])
def read_meal_history(user_id: int, db: Session = Depends(get_db)):
    return get_meal_history(db, user_id)

@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, profile: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        user.profile = profile
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Profile update failed: {str(e)}")
    
@router.post("/{user_id}/log_meal")
def log_user_meal(
    user_id: int, 
    meal_data: Dict[str, Any] = Body(...), 
    db: Session = Depends(get_db)
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        meal = log_meal(
            db, 
            user_id, 
            meal_data.get('analysis_data', {}),
            meal_data.get('portion_estimates', {}),
            meal_data.get('nutrition_summary', {}),
            meal_data.get('recommendations', {})
        )
        return {"message": "Meal logged successfully", "meal_id": meal.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to log meal: {str(e)}")
