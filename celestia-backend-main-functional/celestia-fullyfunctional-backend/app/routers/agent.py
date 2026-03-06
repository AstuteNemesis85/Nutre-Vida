from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.agent_service import HealthCoachAgent
from typing import Dict, Any
import asyncio

router = APIRouter()

@router.post("/chat")
async def chat_with_agent(
    request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Chat with the AI health coach agent
    """
    try:
        message = request.get("message", "")
        context = request.get("context", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Initialize agent with database session
        agent = HealthCoachAgent(db)
        
        # Get response from agent
        response = await agent.chat(message, context)
        
        return {"response": response}
        
    except Exception as e:
        print(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/daily_tip/{user_id}")
def get_daily_tip(user_id: int, db: Session = Depends(get_db)):
    """
    Get a personalized daily health tip
    """
    try:
        agent = HealthCoachAgent(db)
        user_context = agent.get_user_context(user_id)
        tip = agent.generate_daily_tip(user_context)
        
        return {"tip": tip}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tip: {str(e)}")

@router.get("/insights/{user_id}")
def get_user_insights(user_id: int, db: Session = Depends(get_db)):
    """
    Get nutritional insights and recommendations based on user's history
    """
    try:
        agent = HealthCoachAgent(db)
        user_context = agent.get_user_context(user_id)
        
        # Generate insights
        insights = {
            "weekly_stats": user_context.get("weekly_stats", {}),
            "profile": user_context.get("profile", {}),
            "meals_tracked": user_context.get("recent_meals", 0),
            "motivational_message": agent.generate_motivational_message(user_context)
        }
        
        # Add recommendations based on stats
        if user_context.get("weekly_stats"):
            stats = user_context["weekly_stats"]
            recommendations = []
            
            if stats.get("avg_daily_calories", 0) < 1500:
                recommendations.append("Your calorie intake seems low. Ensure you're eating enough to support your daily activities.")
            elif stats.get("avg_daily_calories", 0) > 2500:
                recommendations.append("Your calorie intake is quite high. Consider portion control if weight management is a goal.")
            
            if stats.get("avg_daily_protein", 0) < 50:
                recommendations.append("Try to increase protein intake for better satiety and muscle health.")
            
            insights["recommendations"] = recommendations
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")