from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.services.enhanced_agent_service import EnhancedAgenticService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.smart_notification_service import SmartNotificationService
from app.services.intelligent_meal_planner import IntelligentMealPlanner
from app.services.conversation_memory_service import ConversationMemoryService

router = APIRouter(prefix="/agentic", tags=["Agentic AI"])

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    response_type: str
    session_id: str
    contextual_insights: Dict[str, Any]
    proactive_features: Dict[str, Any]
    suggested_actions: List[str]
    meal_plan_suggestion: Optional[Dict[str, Any]]
    urgent_alerts: List[Dict[str, Any]]
    confidence: float
    timestamp: str

class MealPlanRequest(BaseModel):
    plan_type: str = "weekly"
    duration_days: int = 7
    goals: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    notifications_generated: int
    notifications: List[Dict[str, Any]]
    generation_date: str

@router.post("/chat/{user_id}", response_model=ChatResponse)
async def enhanced_chat(
    user_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Enhanced AI chat with full agentic capabilities including:
    - Contextual conversation memory
    - Proactive health monitoring
    - Smart notifications
    - Intelligent meal planning suggestions
    """
    try:
        enhanced_service = EnhancedAgenticService(db)
        
        result = await enhanced_service.enhanced_chat(
            user_id=user_id,
            message=chat_request.message,
            session_id=chat_request.session_id,
            context=chat_request.context
        )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced chat error: {str(e)}")

@router.get("/dashboard/{user_id}")
async def get_health_dashboard(user_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive health dashboard with all agentic insights including:
    - Conversation insights and patterns
    - Active health alerts and monitoring
    - Smart notifications status
    - Meal planning progress
    - Personalized recommendations
    """
    try:
        enhanced_service = EnhancedAgenticService(db)
        dashboard = enhanced_service.get_user_health_dashboard(user_id)
        
        if dashboard.get('error'):
            raise HTTPException(status_code=500, detail=dashboard['error'])
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@router.post("/meal-plan/{user_id}")
async def create_intelligent_meal_plan(
    user_id: int,
    meal_plan_request: MealPlanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create an intelligent, personalized meal plan using AI that considers:
    - User's eating patterns and preferences
    - Nutritional goals and health objectives
    - Food history and dietary restrictions
    - Seasonal and cultural preferences
    """
    try:
        enhanced_service = EnhancedAgenticService(db)
        
        plan_preferences = {
            'plan_type': meal_plan_request.plan_type,
            'duration_days': meal_plan_request.duration_days,
            'goals': meal_plan_request.goals
        }
        
        result = enhanced_service.create_intelligent_meal_plan(
            user_id=user_id,
            plan_preferences=plan_preferences
        )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Generate notifications in background
        background_tasks.add_task(
            _generate_meal_plan_notifications,
            user_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meal plan creation error: {str(e)}")

@router.get("/meal-plans/{user_id}")
async def get_user_meal_plans(
    user_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all meal plans for a user"""
    try:
        meal_planner = IntelligentMealPlanner(db)
        plans = meal_planner.get_user_meal_plans(user_id, active_only)
        
        return {
            'user_id': user_id,
            'meal_plans': plans,
            'total_plans': len(plans)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting meal plans: {str(e)}")

@router.get("/meal-plan/{meal_plan_id}/details")
async def get_meal_plan_details(
    meal_plan_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific meal plan"""
    try:
        meal_planner = IntelligentMealPlanner(db)
        details = meal_planner.get_meal_plan_details(meal_plan_id, user_id)
        
        if details.get('error'):
            raise HTTPException(status_code=404, detail=details['error'])
        
        return details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting meal plan details: {str(e)}")

@router.post("/meal-plan/complete-meal/{meal_item_id}")
async def mark_meal_completed(
    meal_item_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Mark a meal plan item as completed"""
    try:
        meal_planner = IntelligentMealPlanner(db)
        success = meal_planner.mark_meal_completed(meal_item_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Meal item not found or not accessible")
        
        return {
            'success': True,
            'message': 'Meal marked as completed',
            'meal_item_id': meal_item_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking meal completed: {str(e)}")

@router.get("/health-monitoring/{user_id}")
async def run_health_monitoring(user_id: int, db: Session = Depends(get_db)):
    """
    Run comprehensive health monitoring and get results including:
    - Nutritional pattern analysis
    - Eating behavior monitoring
    - Goal adherence tracking
    - Health risk assessment
    - Predictive insights
    """
    try:
        health_monitor = HealthMonitoringService(db)
        results = health_monitor.run_health_monitoring(user_id)
        
        if results.get('error'):
            raise HTTPException(status_code=500, detail=results['error'])
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health monitoring error: {str(e)}")

@router.get("/alerts/{user_id}")
async def get_health_alerts(user_id: int, db: Session = Depends(get_db)):
    """Get all active health alerts for a user"""
    try:
        health_monitor = HealthMonitoringService(db)
        alerts = health_monitor.get_active_alerts(user_id)
        
        return {
            'user_id': user_id,
            'active_alerts': alerts,
            'total_alerts': len(alerts),
            'urgent_alerts': len([a for a in alerts if a['severity'] in ['high', 'critical']])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

@router.post("/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Dismiss a specific health alert"""
    try:
        health_monitor = HealthMonitoringService(db)
        success = health_monitor.dismiss_alert(user_id, alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or not accessible")
        
        return {
            'success': True,
            'message': 'Alert dismissed',
            'alert_id': alert_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error dismissing alert: {str(e)}")

@router.post("/alerts/{alert_id}/mark-read")
async def mark_alert_read(
    alert_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Mark a health alert as read"""
    try:
        health_monitor = HealthMonitoringService(db)
        success = health_monitor.mark_alert_read(user_id, alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or not accessible")
        
        return {
            'success': True,
            'message': 'Alert marked as read',
            'alert_id': alert_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking alert as read: {str(e)}")

@router.post("/notifications/generate/{user_id}", response_model=NotificationResponse)
async def generate_smart_notifications(user_id: int, db: Session = Depends(get_db)):
    """
    Generate personalized smart notifications including:
    - Meal timing reminders based on eating patterns
    - Hydration reminders
    - Goal check-ins
    - Health tips
    - Meal planning reminders
    """
    try:
        notification_service = SmartNotificationService(db)
        results = notification_service.generate_smart_notifications(user_id)
        
        if results.get('error'):
            raise HTTPException(status_code=500, detail=results['error'])
        
        return NotificationResponse(**results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification generation error: {str(e)}")

@router.get("/notifications/{user_id}")
async def get_pending_notifications(user_id: int, db: Session = Depends(get_db)):
    """Get all pending notifications for a user"""
    try:
        notification_service = SmartNotificationService(db)
        notifications = notification_service.get_pending_notifications(user_id)
        
        return {
            'user_id': user_id,
            'pending_notifications': notifications,
            'total_notifications': len(notifications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notifications: {str(e)}")

@router.post("/notifications/{notification_id}/mark-sent")
async def mark_notification_sent(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as sent"""
    try:
        notification_service = SmartNotificationService(db)
        success = notification_service.mark_notification_sent(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            'success': True,
            'message': 'Notification marked as sent',
            'notification_id': notification_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as sent: {str(e)}")

@router.get("/conversation-insights/{user_id}")
async def get_conversation_insights(user_id: int, db: Session = Depends(get_db)):
    """
    Get detailed conversation insights and patterns including:
    - Conversation frequency and engagement
    - Common topics and interests
    - Important conversation memories
    - User behavior patterns
    """
    try:
        enhanced_service = EnhancedAgenticService(db)
        insights = enhanced_service.get_conversation_insights(user_id)
        
        if insights.get('error'):
            raise HTTPException(status_code=500, detail=insights['error'])
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation insights: {str(e)}")

@router.get("/conversation-history/{user_id}")
async def get_conversation_history(
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get conversation history for a user, optionally filtered by session"""
    try:
        memory_service = ConversationMemoryService(db)
        
        if session_id:
            history = memory_service.get_session_history(user_id, session_id, limit)
        else:
            history = memory_service.get_contextual_memory(user_id, limit=limit)
        
        return {
            'user_id': user_id,
            'session_id': session_id,
            'conversation_history': history,
            'total_messages': len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")

@router.post("/conversation-history/search/{user_id}")
async def search_conversation_history(
    user_id: int,
    search_query: str,
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Search through conversation history using keywords"""
    try:
        memory_service = ConversationMemoryService(db)
        results = memory_service.search_conversation_history(user_id, search_query, limit)
        
        return {
            'user_id': user_id,
            'search_query': search_query,
            'search_results': results,
            'total_results': len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching conversation history: {str(e)}")

@router.post("/cleanup/{user_id}")
async def cleanup_old_data(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    days_old: int = 30
):
    """Clean up old data across all agentic services"""
    try:
        enhanced_service = EnhancedAgenticService(db)
        
        # Run cleanup in background
        background_tasks.add_task(
            _cleanup_user_data,
            days_old
        )
        
        return {
            'message': f'Cleanup initiated for data older than {days_old} days',
            'user_id': user_id,
            'cleanup_scheduled': True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating cleanup: {str(e)}")

@router.get("/status")
async def get_agentic_status():
    """Get status of all agentic AI services"""
    return {
        'agentic_ai_status': 'active',
        'services': {
            'enhanced_chat': 'available',
            'health_monitoring': 'available',
            'smart_notifications': 'available',
            'intelligent_meal_planning': 'available',
            'conversation_memory': 'available'
        },
        'features': [
            'Contextual conversation memory across sessions',
            'Proactive health monitoring with alerts',
            'Smart notification system for meal timing',
            'Intelligent meal planning agent',
            'Predictive health analytics'
        ],
        'version': '1.0.0',
        'last_updated': '2025-01-22'
    }

# Background task functions
async def _generate_meal_plan_notifications(user_id: int):
    """Background task to generate notifications for new meal plan"""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            notification_service = SmartNotificationService(db)
            notification_service.generate_smart_notifications(user_id)
        finally:
            db.close()
    except Exception as e:
        print(f"Error generating meal plan notifications: {e}")

async def _cleanup_user_data(days_old: int):
    """Background task to cleanup old data"""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            enhanced_service = EnhancedAgenticService(db)
            enhanced_service.cleanup_old_data(days_old)
        finally:
            db.close()
    except Exception as e:
        print(f"Error during data cleanup: {e}")
