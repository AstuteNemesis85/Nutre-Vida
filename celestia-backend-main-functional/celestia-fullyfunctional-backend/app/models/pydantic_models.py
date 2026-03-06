from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    profile: Optional[Dict[str, Any]] = {}

class User(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    profile: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AnalysisResponse(BaseModel):
    items: List[Dict[str, Any]]
    total_calories: Optional[int] = 0
    confidence_overall: Optional[int] = 50
    unclear_items: List[str] = []
    need_clarification: bool = False
    total_protein: Optional[int] = 0
    total_carbs: Optional[int] = 0
    total_fat: Optional[int] = 0

class MealLog(BaseModel):
    id: int
    analysis_data: Optional[Dict[str, Any]] = {}
    portion_estimates: Optional[Dict[str, Any]] = {}
    nutrition_summary: Optional[Dict[str, Any]] = {}
    recommendations: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True