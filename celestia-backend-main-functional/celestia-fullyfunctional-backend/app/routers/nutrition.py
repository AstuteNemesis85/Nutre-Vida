from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.nutrition_service import nutrition_lookup, detailed_nutrition_breakdown

router = APIRouter()

@router.post("/lookup")
def get_nutrition(analysis_data: Dict[str, Any]):
    try:
        summary = nutrition_lookup(analysis_data)
        if not summary:
            raise HTTPException(status_code=500, detail="Nutrition lookup failed")
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nutrition lookup error: {str(e)}")

@router.post("/breakdown")
def get_nutrition_breakdown(analysis_data: Dict[str, Any]):
    try:
        breakdown = detailed_nutrition_breakdown(analysis_data)
        if not breakdown:
            raise HTTPException(status_code=500, detail="Nutrition breakdown failed")
        return breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nutrition breakdown error: {str(e)}")
