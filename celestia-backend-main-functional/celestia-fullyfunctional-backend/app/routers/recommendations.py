from typing import Any, Dict

from app.database import get_db
from app.services.nutrition_insights_service import get_nutrition_insights
from app.services.nutrition_service import nutrition_lookup
from app.services.recommendations_service import (healthy_swaps,
                                                  meal_plan_generator,
                                                  personalized_recommendations,
                                                  recipe_generation,
                                                  recipe_modification)
from app.services.user_service import get_user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/swaps")
def get_swaps(analysis_data: Dict[str, Any]):
    try:
        swaps = healthy_swaps(analysis_data)
        return {"swaps": swaps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get swaps: {str(e)}")

@router.post("/personalized/{user_id}")
def get_personalized(analysis_data: Dict[str, Any], user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        recs = personalized_recommendations(analysis_data, user.profile)
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personalized recommendations: {str(e)}")

@router.post("/recipe")
def generate_recipe(analysis_data: Dict[str, Any]):
    try:
        recipe = recipe_generation(analysis_data)
        return {"recipe": recipe}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recipe: {str(e)}")

@router.post("/recipe/modify")
def modify_recipe(request: Dict[str, Any]):
    try:
        original_recipe = request.get("original_recipe", "")
        user_feedback = request.get("user_feedback", "")
        analysis_data = request.get("analysis_data", {})
        
        if not original_recipe or not user_feedback:
            raise HTTPException(status_code=400, detail="Original recipe and user feedback are required")
        
        modified_recipe = recipe_modification(original_recipe, user_feedback, analysis_data)
        return {"recipe": modified_recipe}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify recipe: {str(e)}")

@router.post("/nutrition-insights")
def get_insights(analysis_data: Dict[str, Any]):
    try:
        insights = get_nutrition_insights(analysis_data)
        
        # Ensure the response has the proper structure
        if "error" in insights:
            # Return a structured error response instead of raising HTTPException
            return {
                "macro_balance": {"status": "error", "details": insights.get("details", "Analysis failed"), "recommendations": []},
                "micronutrients": {"highlights": [], "deficiencies": []},
                "health_benefits": [],
                "concerns": ["Unable to analyze nutrition data"],
                "recommendations": ["Please try again or check your input data"]
            }
            
        return insights
    except Exception as e:
        # Return structured error response instead of raising HTTPException
        return {
            "macro_balance": {"status": "error", "details": f"Analysis failed: {str(e)}", "recommendations": []},
            "micronutrients": {"highlights": [], "deficiencies": []},
            "health_benefits": [],
            "concerns": ["Service temporarily unavailable"],
            "recommendations": ["Please try again later"]
        }

@router.get("/meal_plan/{user_id}")
@router.post("/meal_plan/{user_id}")
def generate_meal_plan(user_id: int, profile: Dict[str, Any] = None, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        used_profile = profile if profile else user.profile
        plan = meal_plan_generator(used_profile)
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate meal plan: {str(e)}")

@router.post("/reanalyze-edited-items")
def reanalyze_edited_items(request: Dict[str, Any]):
    """
    Reanalyze edited food items through Gemini for updated nutritional information.
    Expected request format:
    {
        "edited_items": [{"name": "food name", "quantity": "portion"}],
        "clarifications": "optional additional notes"
    }
    """
    try:
        edited_items = request.get("edited_items", [])
        clarifications = request.get("clarifications", "")
        
        if not edited_items:
            raise HTTPException(status_code=400, detail="No edited items provided")
        
        # Create analysis data structure
        analysis_data = {
            "items": edited_items,
            "clarifications": clarifications
        }
        
        # Get comprehensive nutrition analysis from Gemini
        nutrition_result = nutrition_lookup(analysis_data)
        
        # Ensure the result has all required fields
        if not nutrition_result.get("items"):
            # Fallback: create basic structure from input
            nutrition_result = {
                "items": edited_items,
                "total_calories": 0,
                "total_protein": 0,
                "total_carbs": 0,
                "total_fat": 0,
                "totals": {
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0
                }
            }
        
        return nutrition_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reanalyze edited items: {str(e)}")
