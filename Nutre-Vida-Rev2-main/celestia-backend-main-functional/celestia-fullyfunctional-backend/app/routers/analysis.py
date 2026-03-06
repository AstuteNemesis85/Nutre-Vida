def clean_session_data(session: dict) -> dict:
    # Utility to remove non-serializable objects (like PIL Image) from session data
    data = dict(session)
    if 'image' in data:
        data['image'] = None
    return data

import io
from typing import Any, Dict, List, Optional

from app.database import get_db
from app.models.pydantic_models import AnalysisResponse
from app.routers.sessions import sessions
from app.services.analysis_service import (analyze_food_image, explainability,
                                           generate_clarifying_questions,
                                           portion_estimation,
                                           refine_analysis_with_answers)
from app.services.nutrition_service import nutrition_lookup
from app.services.recommendations_service import (healthy_swaps,
                                                  personalized_recommendations)
from app.services.user_service import get_user, log_meal
from fastapi import (APIRouter, Body, Depends, File, HTTPException, Query,
                     UploadFile)
from PIL import Image
from sqlalchemy.orm import Session

router = APIRouter()

    

def validate_session(session_id: str):
    if session_id not in sessions:
        # Create a new session if it doesn't exist
        sessions[session_id] = {
            "step": "upload",
            "image": None,
            "analysis_data": None,
            "questions": [],
            "user_answers": [],
            "portion_estimates": None,
            "nutrition_summary": None,
            "recommendations": None
        }
    return sessions[session_id]


@router.post("/upload/{session_id}")
async def upload_image(session_id: str, file: UploadFile = File(...)):
    session = validate_session(session_id)
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        image = Image.open(io.BytesIO(image_bytes))
        sessions[session_id]["image"] = image
        sessions[session_id]["step"] = "analyze"
        return {"message": "Image uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")


@router.post("/analyze/{session_id}")
async def analyze(session_id: str, user_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    session = validate_session(session_id)
    image = sessions[session_id].get("image")
    if image is None:
        raise HTTPException(status_code=400, detail="No image uploaded for this session.")
    try:
        # Get user profile for dietary preferences
        user_profile = {}
        if user_id:
            user = get_user(db, user_id)
            if user:
                user_profile = user.profile

        # Analyze image with user profile
        analysis_data = analyze_food_image(image, user_profile)
        if not analysis_data or not analysis_data.get('items'):
            return {
                "message": "Analysis failed - no food detected",
                "data": {
                    "analysis_data": {
                        "items": [],
                        "total_calories": 0,
                        "total_protein": 0,
                        "total_carbs": 0,
                        "total_fat": 0,
                        "confidence_overall": 0,
                        "need_clarification": True,
                        "unclear_items": ["No food items detected. Please try a clearer image."]
                    }
                }
            }

        sessions[session_id]["analysis_data"] = analysis_data

        # Process additional data
        portion_estimates = portion_estimation(analysis_data)
        sessions[session_id]["portion_estimates"] = portion_estimates

        nutrition_summary = nutrition_lookup(analysis_data)
        sessions[session_id]["nutrition_summary"] = nutrition_summary

        # Get recommendations
        swaps = healthy_swaps(analysis_data)
        recommendations = {"swaps": swaps}

        if user_id:
            user = get_user(db, user_id)
            if user:
                personalized = personalized_recommendations(analysis_data, user.profile)
                recommendations["personalized"] = personalized
                try:
                    log_meal(db, user_id, analysis_data, portion_estimates, nutrition_summary, recommendations)
                except Exception as e:
                    print(f"Failed to log meal: {e}")

        sessions[session_id]["recommendations"] = recommendations

        # Check if clarification needed
        if analysis_data.get('need_clarification', False):
            questions = generate_clarifying_questions(analysis_data)
            sessions[session_id]["questions"] = questions
            sessions[session_id]["step"] = "clarify"
            return {
                "message": "Analysis complete, clarification needed",
                "questions": questions
            }
        else:
            sessions[session_id]["step"] = "results"
            return {
                "message": "Analysis complete",
                "data": {
                    "analysis_data": analysis_data,
                    "recommendations": recommendations
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/skip_clarification/{session_id}")
def skip_clarification(session_id: str):
    session = validate_session(session_id)
    
    try:
        sessions[session_id]["step"] = "results"
        return {"message": "Clarification skipped", "data": clean_session_data(sessions[session_id])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skip clarification failed: {str(e)}")

@router.get("/results/{session_id}")
def get_results(session_id: str):
    session = validate_session(session_id)
    
    analysis_data = sessions[session_id].get("analysis_data")
    if not analysis_data:
        raise HTTPException(status_code=400, detail="No analysis data found")
    
    try:
        # Ensure totals are calculated
        items = analysis_data.get('items', [])
        analysis_data["total_protein"] = sum(item.get('protein', 0) for item in items)
        analysis_data["total_carbs"] = sum(item.get('carbs', 0) for item in items)
        analysis_data["total_fat"] = sum(item.get('fat', 0) for item in items)
        
        if "total_calories" not in analysis_data:
            analysis_data["total_calories"] = sum(item.get('calories', 0) for item in items)
        
        return analysis_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

@router.get("/explanation/{session_id}")
def get_explanation(session_id: str):
    session = validate_session(session_id)
    
    analysis_data = sessions[session_id].get("analysis_data")
    if not analysis_data:
        raise HTTPException(status_code=400, detail="No analysis data found")
    
    try:
        explanation = explainability(analysis_data)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get explanation: {str(e)}")
    
@router.post("/analyze_text/{session_id}")
def analyze_text(
    session_id: str, 
    text: dict = Body(...), 
    user_id: Optional[int] = Query(None), 
    db: Session = Depends(get_db)
):
    session = validate_session(session_id)
    
    dish_text = text.get("text", "").strip()
    if not dish_text:
        raise HTTPException(status_code=400, detail="No dish text provided")
    
    try:
        # Get user profile for dietary preferences
        user_profile = {}
        if user_id:
            user = get_user(db, user_id)
            if user:
                user_profile = user.profile
        
        # Analyze text with user profile
        analysis_data = analyze_food_image(dish_text, user_profile)
        if not analysis_data or not analysis_data.get('items'):
            raise HTTPException(status_code=500, detail="Text analysis failed - no items detected")
        
        sessions[session_id]["analysis_data"] = analysis_data
        
        # Process additional data
        portion_estimates = portion_estimation(analysis_data)
        sessions[session_id]["portion_estimates"] = portion_estimates
        
        nutrition_summary = nutrition_lookup(analysis_data)
        sessions[session_id]["nutrition_summary"] = nutrition_summary
        
        # Get recommendations
        swaps = healthy_swaps(analysis_data)
        recommendations = {"swaps": swaps}
        
        if user_id:
            user = get_user(db, user_id)
            if user:
                personalized = personalized_recommendations(analysis_data, user.profile)
                recommendations["personalized"] = personalized
                try:
                    log_meal(db, user_id, analysis_data, portion_estimates, nutrition_summary, recommendations)
                except Exception as e:
                    print(f"Failed to log meal: {e}")
        
        sessions[session_id]["recommendations"] = recommendations
        
        # Check if clarification needed
        if analysis_data.get('need_clarification', False):
            questions = generate_clarifying_questions(analysis_data)
            sessions[session_id]["questions"] = questions
            sessions[session_id]["step"] = "clarify"
            return {
                "message": "Analysis complete, clarification needed",
                "questions": questions
            }
        else:
            sessions[session_id]["step"] = "results"
            return {
                "message": "Analysis complete", 
                "data": {
                    "analysis_data": analysis_data,
                    "recommendations": recommendations
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
@router.post("/refine/{session_id}")
def refine_analysis(session_id: str, answers: List[str] = Body(...)):
    session = validate_session(session_id)
    questions = sessions[session_id].get("questions", [])
    # Allow single answer for bulk edit/refinement
    if len(answers) != len(questions):
        if len(answers) == 1 and len(questions) > 0:
            # Use the single answer for all questions (bulk correction)
            answers = [answers[0]] * len(questions)
        else:
            raise HTTPException(status_code=400, detail="Mismatch in number of answers")
    try:
        original_data = sessions[session_id]["analysis_data"]
        refined_data = refine_analysis_with_answers(original_data, questions, answers)
        if not refined_data:
            refined_data = original_data
        sessions[session_id]["analysis_data"] = refined_data
        sessions[session_id]["step"] = "results"
        return {"message": "Analysis refined", "data": clean_session_data(sessions[session_id])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis refinement failed: {str(e)}")
