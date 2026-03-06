from typing import Any, Dict, List, Optional

from app.database import get_db
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.enhanced_agent_service import EnhancedAgenticService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.intelligent_meal_planner import IntelligentMealPlanner
from app.services.smart_notification_service import SmartNotificationService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
        # Get user profile for personalization
        from app.models.db_models import User
        user = db.query(User).filter(User.id == user_id).first()
        
        # Extract preferences from request and user profile
        goals = meal_plan_request.goals or {}
        duration_days = meal_plan_request.duration_days
        
        # Enhance goals with user profile data
        if user and user.profile:
            user_profile = user.profile
            if not goals.get('dietary_restrictions') and user_profile.get('diet_preference'):
                goals['dietary_restrictions'] = user_profile.get('diet_preference')
            if not goals.get('calorie_target') and user.daily_goals and user.daily_goals.get('calories'):
                goals['calorie_target'] = user.daily_goals.get('calories')
        
        # Log the preferences for debugging
        print(f"Generating meal plan for user {user_id} with preferences: {goals}")
        print(f"Duration: {duration_days} days")
        
        # Create AI-generated personalized meal plan
        meal_plan = _create_direct_meal_plan(duration_days, goals)
        
        # Generate notifications in background
        background_tasks.add_task(
            _generate_meal_plan_notifications,
            user_id,
            db
        )
        
        return {'meal_plan': meal_plan}
        
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
            enhanced_service,
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
async def _generate_meal_plan_notifications(user_id: int, db: Session):
    """Background task to generate notifications for new meal plan"""
    try:
        notification_service = SmartNotificationService(db)
        notification_service.generate_smart_notifications(user_id)
    except Exception as e:
        print(f"Error generating meal plan notifications: {e}")

async def _cleanup_user_data(enhanced_service: EnhancedAgenticService, days_old: int):
    """Background task to cleanup old data"""
    try:
        enhanced_service.cleanup_old_data(days_old)
    except Exception as e:
        print(f"Error during data cleanup: {e}")

def _format_meal_plan_for_frontend(backend_result: Dict[str, Any]) -> Dict[str, Any]:
    """Transform backend meal plan format to frontend-expected format"""
    try:
        # Get meal items from the backend result
        meal_items = backend_result.get('meal_items', [])
        duration_days = backend_result.get('duration_days', 7)
        
        # If meal_items is empty, create a simple structure based on meal_plan_data
        if not meal_items:
            return _create_simple_meal_plan_structure(backend_result)
        
        # Group meal items by day
        days_data = {}
        
        for item in meal_items:
            day_key = item.get('day_of_plan', 1)
            meal_type = item.get('meal_type', 'breakfast')
            
            if day_key not in days_data:
                days_data[day_key] = {
                    'day': f'Day {day_key}',
                    'meals': {}
                }
            
            if meal_type not in days_data[day_key]['meals']:
                days_data[day_key]['meals'][meal_type] = []
            
            # Add the meal item with proper formatting
            days_data[day_key]['meals'][meal_type].append({
                'name': item.get('meal_name', f'{meal_type.title()} Item'),
                'calories': item.get('estimated_calories', '400')
            })
        
        # Convert to array format expected by frontend
        days_array = []
        for day_num in range(1, duration_days + 1):
            if day_num in days_data:
                days_array.append(days_data[day_num])
            else:
                # Create empty day structure
                days_array.append({
                    'day': f'Day {day_num}',
                    'meals': {
                        'breakfast': [{'name': 'Planned meal coming soon', 'calories': '400'}],
                        'lunch': [{'name': 'Planned meal coming soon', 'calories': '600'}],
                        'dinner': [{'name': 'Planned meal coming soon', 'calories': '500'}]
                    }
                })
        
        return {'days': days_array}
        
    except Exception as e:
        print(f"Error formatting meal plan: {e}")
        return _create_fallback_meal_plan(backend_result.get('duration_days', 7))

def _create_simple_meal_plan_structure(backend_result: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simple meal plan structure when detailed items aren't available"""
    duration_days = backend_result.get('duration_days', 7)
    meal_plan_data = backend_result.get('meal_plan_data', {})
    daily_structure = meal_plan_data.get('daily_structure', {})
    weekly_themes = meal_plan_data.get('weekly_themes', {})
    
    days_array = []
    
    for day_num in range(1, duration_days + 1):
        day_theme = weekly_themes.get(f'day_{day_num}', 'balanced')
        
        day_meals = {}
        for meal_type, meal_config in daily_structure.items():
            if meal_type in ['breakfast', 'lunch', 'dinner']:
                target_calories = meal_config.get('target_calories', 500)
                
                # Create themed meal names based on day theme
                meal_name = _generate_themed_meal_name(meal_type, day_theme, day_num)
                
                day_meals[meal_type] = [{
                    'name': meal_name,
                    'calories': str(target_calories)
                }]
        
        days_array.append({
            'day': f'Day {day_num}',
            'meals': day_meals
        })
    
    return {'days': days_array}

def _generate_themed_meal_name(meal_type: str, theme: str, day_num: int) -> str:
    """Generate a themed meal name based on meal type and day theme"""
    
    themed_meals = {
        'traditional_comfort': {
            'breakfast': ['Masala Oats with Milk', 'Paratha with Curd', 'Idli Sambhar'],
            'lunch': ['Dal Chawal with Sabzi', 'Chole Bhature', 'Rajma Rice'],
            'dinner': ['Roti with Dal and Sabzi', 'Khichdi with Papad', 'Rice with Curry']
        },
        'protein_power': {
            'breakfast': ['Protein Smoothie Bowl', 'Egg Bhurji with Toast', 'Greek Yogurt with Nuts'],
            'lunch': ['Grilled Chicken Salad', 'Paneer Tikka Wrap', 'Lentil Soup with Bread'],
            'dinner': ['Fish Curry with Rice', 'Dal Tadka with Quinoa', 'Chicken Stir-fry']
        },
        'veggie_delight': {
            'breakfast': ['Vegetable Poha', 'Spinach Paratha', 'Mixed Fruit Bowl'],
            'lunch': ['Rainbow Salad Bowl', 'Vegetable Pulao', 'Stuffed Capsicum'],
            'dinner': ['Mixed Vegetable Curry', 'Palak Paneer with Roti', 'Vegetable Biryani']
        },
        'grain_goodness': {
            'breakfast': ['Quinoa Porridge', 'Millet Upma', 'Oats Idli'],
            'lunch': ['Brown Rice Bowl', 'Bajra Roti Meal', 'Jowar Khichdi'],
            'dinner': ['Whole Wheat Pasta', 'Ragi Dosa with Sambhar', 'Barley Soup']
        },
        'light_fresh': {
            'breakfast': ['Fresh Fruit Salad', 'Smoothie Bowl', 'Yogurt Parfait'],
            'lunch': ['Grilled Vegetable Salad', 'Soup and Salad Combo', 'Fresh Wrap'],
            'dinner': ['Light Vegetable Soup', 'Steamed Vegetables', 'Herbal Rice Bowl']
        },
        'regional_special': {
            'breakfast': ['South Indian Breakfast', 'Punjabi Style Paratha', 'Bengali Style Poha'],
            'lunch': ['Gujarati Thali', 'Maharashtrian Meal', 'Kerala Fish Curry'],
            'dinner': ['Rajasthani Dal Baati', 'Tamil Nadu Meal', 'Bengali Fish Rice']
        },
        'fusion_healthy': {
            'breakfast': ['Avocado Toast Indian Style', 'Quinoa Upma', 'Chia Pudding'],
            'lunch': ['Mediterranean Indian Bowl', 'Asian Fusion Salad', 'Healthy Wrap'],
            'dinner': ['Indo-Italian Pasta', 'Asian Stir-fry', 'Mediterranean Curry']
        }
    }
    
    # Get meals for the theme, fallback to balanced if theme not found
    theme_meals = themed_meals.get(theme, {
        'breakfast': ['Healthy Breakfast', 'Nutritious Morning Meal', 'Balanced Breakfast'],
        'lunch': ['Wholesome Lunch', 'Balanced Midday Meal', 'Nutritious Lunch'],
        'dinner': ['Healthy Dinner', 'Light Evening Meal', 'Balanced Dinner']
    })
    
    # Get meals for the meal type, fallback to generic if not found
    meal_options = theme_meals.get(meal_type, ['Healthy Meal', 'Nutritious Option', 'Balanced Dish'])
    
    # Select based on day to ensure variety
    selected_meal = meal_options[(day_num - 1) % len(meal_options)]
    
    return selected_meal

def _create_fallback_meal_plan(duration_days: int = 7) -> Dict[str, Any]:
    """Create a fallback meal plan structure when all else fails"""
    days_array = []
    
    for day_num in range(1, duration_days + 1):
        days_array.append({
            'day': f'Day {day_num}',
            'meals': {
                'breakfast': [{'name': 'Healthy Breakfast Option', 'calories': '400'}],
                'lunch': [{'name': 'Balanced Lunch Meal', 'calories': '600'}],
                'dinner': [{'name': 'Light Dinner Option', 'calories': '500'}]
            }
        })
    
    return {'days': days_array}

def _create_direct_meal_plan(duration_days: int, goals: Dict[str, Any]) -> Dict[str, Any]:
    """Create a personalized meal plan using Gemini AI based on user preferences"""
    try:
        import google.generativeai as genai
        from app.config import settings

        # Configure Gemini AI
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        
        # Extract preferences from goals
        calorie_target = goals.get('calorie_target', 2000)
        dietary_restrictions = goals.get('dietary_restrictions', 'No restrictions')
        cuisine_preference = goals.get('cuisine_preference', 'Indian')
        meals_per_day = goals.get('meals_per_day', 3)
        budget = goals.get('budget', 'Medium')
        
        # Create comprehensive prompt for Gemini
        prompt = f"""
        Generate a personalized {duration_days}-day Indian meal plan with the following preferences:
        
        USER PREFERENCES:
        - Daily Calorie Target: {calorie_target} calories
        - Dietary Restrictions: {dietary_restrictions}
        - Cuisine Preference: {cuisine_preference}
        - Meals Per Day: {meals_per_day}
        - Budget: {budget}
        
        REQUIREMENTS:
        1. Generate exactly {duration_days} days of meals
        2. Each day should have breakfast, lunch, and dinner
        3. All meals should be authentic Indian dishes
        4. Provide calorie count for each meal
        5. Consider the dietary restrictions strictly
        6. Vary meals across days for nutritional balance
        7. Keep within budget constraints ({budget} budget)
        
        MEAL DISTRIBUTION:
        - Breakfast: 25% of daily calories (~{int(calorie_target * 0.25)} cal)
        - Lunch: 40% of daily calories (~{int(calorie_target * 0.4)} cal)  
        - Dinner: 35% of daily calories (~{int(calorie_target * 0.35)} cal)
        
        DIETARY GUIDELINES:
        - If Vegetarian: No meat, fish, or eggs
        - If Vegan: No animal products at all
        - If Gluten-Free: No wheat, avoid roti/chapati, use rice alternatives
        - If Keto: High fat, low carb, minimize rice/roti
        - If Diabetic-Friendly: Low sugar, complex carbs, portion control
        
        FORMAT: Return ONLY a valid JSON object with this exact structure:
        {{
          "days": [
            {{
              "day": "Day 1",
              "meals": {{
                "breakfast": [{{
                  "name": "Exact meal name with ingredients",
                  "calories": "number only"
                }}],
                "lunch": [{{
                  "name": "Exact meal name with ingredients", 
                  "calories": "number only"
                }}],
                "dinner": [{{
                  "name": "Exact meal name with ingredients",
                  "calories": "number only"
                }}]
              }}
            }}
          ]
        }}
        
        IMPORTANT: 
        - Each meal name should be specific and appetizing
        - Include cooking method and key ingredients
        - Ensure variety across all {duration_days} days
        - All calories should be realistic numbers
        - Strictly follow dietary restrictions
        - Make meals culturally authentic and practical to prepare
        """
        
        # Generate meal plan with Gemini
        response = model.generate_content(prompt)
        meal_plan_text = response.text.strip()
        
        # Clean the response text
        if meal_plan_text.startswith('```json'):
            meal_plan_text = meal_plan_text[7:]
        if meal_plan_text.endswith('```'):
            meal_plan_text = meal_plan_text[:-3]
        meal_plan_text = meal_plan_text.strip()
        
        # Parse the JSON response
        import json
        meal_plan = json.loads(meal_plan_text)
        
        return meal_plan
        
    except Exception as e:
        print(f"Error generating AI meal plan: {e}")
        # Fallback to a basic personalized plan if AI fails
        return _create_personalized_fallback_plan(duration_days, goals)

def _create_personalized_fallback_plan(duration_days: int, goals: Dict[str, Any]) -> Dict[str, Any]:
    """Create a personalized fallback plan based on dietary preferences"""
    
    dietary_restrictions = goals.get('dietary_restrictions', '').lower()
    calorie_target = goals.get('calorie_target', 2000)
    cuisine_preference = goals.get('cuisine_preference', 'Indian')
    
    # Meal options based on dietary restrictions
    if 'vegan' in dietary_restrictions:
        meal_options = {
            'breakfast': [
                {'name': 'Oats Porridge with Almond Milk and Fruits', 'calories': str(int(calorie_target * 0.25))},
                {'name': 'Vegetable Poha with Coconut', 'calories': str(int(calorie_target * 0.25))},
                {'name': 'Quinoa Upma with Vegetables', 'calories': str(int(calorie_target * 0.25))},
            ],
            'lunch': [
                {'name': 'Quinoa Vegetable Bowl with Dal', 'calories': str(int(calorie_target * 0.4))},
                {'name': 'Brown Rice with Mixed Lentil Curry', 'calories': str(int(calorie_target * 0.4))},
                {'name': 'Vegetable Biryani with Coconut Raita', 'calories': str(int(calorie_target * 0.4))},
            ],
            'dinner': [
                {'name': 'Vegetable Soup with Quinoa Salad', 'calories': str(int(calorie_target * 0.35))},
                {'name': 'Dal Tadka with Brown Rice', 'calories': str(int(calorie_target * 0.35))},
                {'name': 'Mixed Vegetable Curry with Millet Roti', 'calories': str(int(calorie_target * 0.35))},
            ]
        }
    elif 'vegetarian' in dietary_restrictions or 'veg' in dietary_restrictions:
        meal_options = {
            'breakfast': [
                {'name': 'Masala Oats with Milk and Nuts', 'calories': str(int(calorie_target * 0.25))},
                {'name': 'Vegetable Paratha with Curd', 'calories': str(int(calorie_target * 0.25))},
                {'name': 'Idli Sambhar with Coconut Chutney', 'calories': str(int(calorie_target * 0.25))},
            ],
            'lunch': [
                {'name': 'Dal Rice with Paneer Sabzi', 'calories': str(int(calorie_target * 0.4))},
                {'name': 'Chole with Rice and Salad', 'calories': str(int(calorie_target * 0.4))},
                {'name': 'Vegetable Pulao with Raita', 'calories': str(int(calorie_target * 0.4))},
            ],
            'dinner': [
                {'name': 'Roti with Dal and Vegetable Curry', 'calories': str(int(calorie_target * 0.35))},
                {'name': 'Khichdi with Ghee and Papad', 'calories': str(int(calorie_target * 0.35))},
                {'name': 'Paneer Curry with Jeera Rice', 'calories': str(int(calorie_target * 0.35))},
            ]
        }
    else:  # No restrictions - include non-veg options
        meal_options = {
            'breakfast': [
                {'name': 'Egg Bhurji with Toast and Tea', 'calories': str(int(calorie_target * 0.25))},
                {'name': 'Masala Oats with Milk', 'calories': str(int(calorie_target * 0.25))},
                {'name': 'Chicken Sausage with Bread', 'calories': str(int(calorie_target * 0.25))},
            ],
            'lunch': [
                {'name': 'Chicken Curry with Rice', 'calories': str(int(calorie_target * 0.4))},
                {'name': 'Fish Curry with Dal Rice', 'calories': str(int(calorie_target * 0.4))},
                {'name': 'Mutton Biryani (small portion)', 'calories': str(int(calorie_target * 0.4))},
            ],
            'dinner': [
                {'name': 'Grilled Chicken with Vegetable Salad', 'calories': str(int(calorie_target * 0.35))},
                {'name': 'Fish Fry with Dal Rice', 'calories': str(int(calorie_target * 0.35))},
                {'name': 'Egg Curry with Roti', 'calories': str(int(calorie_target * 0.35))},
            ]
        }
    
    # Create varied meal plan
    days_array = []
    for day_num in range(1, duration_days + 1):
        breakfast_idx = (day_num - 1) % len(meal_options['breakfast'])
        lunch_idx = (day_num - 1) % len(meal_options['lunch'])
        dinner_idx = (day_num - 1) % len(meal_options['dinner'])
        
        days_array.append({
            'day': f'Day {day_num}',
            'meals': {
                'breakfast': [meal_options['breakfast'][breakfast_idx]],
                'lunch': [meal_options['lunch'][lunch_idx]],
                'dinner': [meal_options['dinner'][dinner_idx]]
            }
        })
    
    return {'days': days_array}
