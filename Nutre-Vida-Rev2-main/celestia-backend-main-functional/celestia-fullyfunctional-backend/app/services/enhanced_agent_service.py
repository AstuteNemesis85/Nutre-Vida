import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from app.config import settings
from app.services.agent_service import HealthCoachAgent
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.intelligent_meal_planner import IntelligentMealPlanner
from app.services.smart_notification_service import SmartNotificationService
from app.services.langgraph_agent import run_health_coach, generate_langgraph_meal_plan
from app.services.rag_service import get_rag_service
from sqlalchemy.orm import Session

# Configure Gemini AI (kept as fallback)
genai.configure(api_key=settings.google_api_key)
enhanced_agent_model = genai.GenerativeModel("models/gemini-2.5-flash")

class EnhancedAgenticService:
    """
    Enhanced Agentic AI Service that integrates all advanced AI capabilities:
    - Contextual conversation memory across sessions
    - Proactive health monitoring with alerts
    - Smart notifications for meal timing
    - Intelligent meal planning
    - Predictive health analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize all agentic services
        self.conversation_memory = ConversationMemoryService(db)
        self.health_monitor = HealthMonitoringService(db)
        self.notification_service = SmartNotificationService(db)
        self.meal_planner = IntelligentMealPlanner(db)
        self.base_agent = HealthCoachAgent(db)
        
        # Session management
        self.active_sessions = {}  # Store active conversation sessions
    
    def _extract_food_items(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract food items from analysis data with proper field name handling"""
        foods = []
        if isinstance(analysis_data, dict):
            # Try multiple possible data structures
            items = analysis_data.get('items', [])
            if not items:
                # Fallback: check if analysis_data itself contains the items
                items = analysis_data if isinstance(analysis_data, list) else []
            
            for item in items:
                if isinstance(item, dict):
                    # Try different field name variants used in your app
                    name = item.get('name') or item.get('food_name') or item.get('item_name') or item.get('foodName')
                    quantity = item.get('quantity', '') or item.get('amount', '')
                    
                    if name:
                        if quantity:
                            foods.append(f"{name} ({quantity})")
                        else:
                            foods.append(name)
        
        return foods

    async def enhanced_chat(
        self, 
        user_id: int, 
        message: str, 
        session_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhanced chat with full agentic capabilities including memory, 
        proactive monitoring, and intelligent responses
        """
        try:
            # Get or create session
            if not session_id:
                session_id = self.conversation_memory.create_session_id()
            
            # Store user message in conversation memory
            user_context = context or {}
            memory_entry = self.conversation_memory.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='user',
                content=message,
                context_data=user_context
            )
            
            # Get contextual memory for enhanced responses
            contextual_memories = self.conversation_memory.get_contextual_memory(
                user_id=user_id,
                current_context=user_context,
                limit=5
            )
            
            # CRITICAL: Get user's actual meal history from database
            # First detect if this is a specific meal history query
            meal_query_info = self._detect_meal_history_query(message)
            
            if meal_query_info['is_meal_history_query']:
                # Get targeted meal data for specific queries
                user_meal_history = self._get_targeted_meal_data(user_id, meal_query_info)
                if user_meal_history.get('formatted_response'):
                    # For specific meal history queries, return the formatted response directly
                    return {
                        'message': user_meal_history['formatted_response'],
                        'response_type': 'meal_history',
                        'session_id': session_id,
                        'contextual_insights': {
                            'memories_used': len(contextual_memories),
                            'health_alerts': 0,
                            'urgent_alerts': 0,
                            'meal_data_retrieved': True
                        },
                        'proactive_features': {
                            'notifications_generated': 0,
                            'meal_plan_suggested': False,
                            'health_insights': 0
                        },
                        'suggested_actions': [],
                        'meal_plan_suggestion': None,
                        'urgent_alerts': [],
                        'confidence': 0.95,
                        'timestamp': datetime.now().isoformat()
                    }
            
            # For general queries, get comprehensive meal history
            user_meal_history = self._get_user_meal_history(user_id)
            user_profile_data = self._get_user_profile_data(user_id)
            
            # Run proactive health monitoring
            monitoring_results = self.health_monitor.run_health_monitoring(user_id)
            
            # Check for any urgent alerts
            active_alerts = self.health_monitor.get_active_alerts(user_id)
            urgent_alerts = [alert for alert in active_alerts if alert['severity'] in ['high', 'critical']]
            
            # Generate enhanced response using all available context
            enhanced_context = {
                **user_context,
                'conversation_history': contextual_memories,
                'health_alerts': active_alerts,
                'monitoring_insights': monitoring_results,
                'user_meal_history': user_meal_history,  # REAL meal data
                'user_profile': user_profile_data,       # REAL user profile
                'session_id': session_id
            }
            
            # Generate AI response with meal history context
            agent_response = await self._generate_enhanced_response(
                user_id=user_id,
                message=message,
                context=enhanced_context
            )
            
            # Store agent response in conversation memory
            self.conversation_memory.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_type='agent',
                content=agent_response['message'],
                context_data={
                    'response_type': agent_response.get('response_type', 'general'),
                    'confidence': agent_response.get('confidence', 0.8),
                    'actions_suggested': agent_response.get('actions', [])
                }
            )
            
            # Generate smart notifications if appropriate
            if agent_response.get('trigger_notifications', False):
                notification_results = self.notification_service.generate_smart_notifications(user_id)
            else:
                notification_results = {'notifications_generated': 0}
            
            # Check if meal planning is needed
            meal_plan_suggestion = None
            if self._should_suggest_meal_planning(message, user_context):
                meal_plan_suggestion = self._generate_meal_plan_suggestion(user_id)
            
            return {
                'message': agent_response['message'],
                'response_type': agent_response.get('response_type', 'general'),
                'session_id': session_id,
                'contextual_insights': {
                    'memories_used': len(contextual_memories),
                    'health_alerts': len(active_alerts),
                    'urgent_alerts': len(urgent_alerts),
                    'monitoring_completed': monitoring_results.get('monitoring_completed', False)
                },
                'proactive_features': {
                    'notifications_generated': notification_results.get('notifications_generated', 0),
                    'meal_plan_suggested': meal_plan_suggestion is not None,
                    'health_insights': monitoring_results.get('insights_generated', 0)
                },
                'suggested_actions': agent_response.get('actions', []),
                'meal_plan_suggestion': meal_plan_suggestion,
                'urgent_alerts': urgent_alerts,
                'confidence': agent_response.get('confidence', 0.8),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in enhanced chat: {e}")
            return {
                'message': "I'm having trouble processing that right now. Could you try again?",
                'response_type': 'error',
                'session_id': session_id or 'unknown',
                'error': str(e)
            }
    
    def _detect_meal_history_query(self, message: str) -> Dict[str, Any]:
        """Detect if user is asking about their meal history and extract timeframe"""
        message_lower = message.lower()
        
        query_info = {
            'is_meal_history_query': False,
            'timeframe': 'recent',  # recent, today, yesterday, week, month
            'specific_request': None
        }
        
        # Detect meal history related queries
        meal_keywords = [
            'what did i eat', 'my meals', 'food history', 'eating pattern',
            'past meals', 'yesterday', 'today', 'this week', 'last week',
            'my food', 'nutrition summary', 'calories consumed', 'my diet',
            'past 5 hours', 'past hours', 'recent hours'
        ]
        
        if any(keyword in message_lower for keyword in meal_keywords):
            query_info['is_meal_history_query'] = True
            
            # Detect timeframe
            if any(word in message_lower for word in ['today', 'this morning', 'this afternoon']):
                query_info['timeframe'] = 'today'
            elif any(word in message_lower for word in ['yesterday', 'last night']):
                query_info['timeframe'] = 'yesterday'
            elif any(word in message_lower for word in ['this week', 'past week', 'weekly']):
                query_info['timeframe'] = 'week'
            elif any(word in message_lower for word in ['past 5 hours', '5 hours', 'recent hours', 'past hours']):
                query_info['timeframe'] = 'recent_hours'
            elif any(word in message_lower for word in ['month', 'monthly', 'past month']):
                query_info['timeframe'] = 'month'
            
            # Detect specific requests
            if any(word in message_lower for word in ['calories', 'calorie']):
                query_info['specific_request'] = 'calories'
            elif any(word in message_lower for word in ['protein', 'proteins']):
                query_info['specific_request'] = 'protein'
            elif any(word in message_lower for word in ['pattern', 'patterns', 'trend']):
                query_info['specific_request'] = 'patterns'
        
        return query_info

    def _get_targeted_meal_data(self, user_id: int, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get targeted meal data based on the user's specific query"""
        try:
            from app.models.db_models import DailySummary, Meal

            # Determine date range based on query
            end_date = datetime.now().date()
            
            if query_info['timeframe'] == 'today':
                start_date = end_date
            elif query_info['timeframe'] == 'yesterday':
                start_date = end_date - timedelta(days=1)
                end_date = start_date
            elif query_info['timeframe'] == 'week':
                start_date = end_date - timedelta(days=7)
            elif query_info['timeframe'] == 'recent_hours':
                # For "past 5 hours" queries
                start_datetime = datetime.now() - timedelta(hours=5)
                meals = self.db.query(Meal).filter(
                    Meal.user_id == user_id,
                    Meal.upload_time >= start_datetime
                ).order_by(Meal.upload_time.desc()).all()
                
                return self._format_recent_hours_meals(meals)
            elif query_info['timeframe'] == 'month':
                start_date = end_date - timedelta(days=30)
            else:  # recent
                start_date = end_date - timedelta(days=3)
            
            # Get meals for the timeframe
            meals = self.db.query(Meal).filter(
                Meal.user_id == user_id,
                Meal.upload_date >= start_date,
                Meal.upload_date <= end_date
            ).order_by(Meal.upload_time.desc()).all()
            
            # Get daily summaries
            summaries = self.db.query(DailySummary).filter(
                DailySummary.user_id == user_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date
            ).all()
            
            return self._format_targeted_meal_response(meals, summaries, query_info)
            
        except Exception as e:
            print(f"Error getting targeted meal data: {e}")
            return {'error': str(e)}

    def _format_recent_hours_meals(self, meals: List) -> Dict[str, Any]:
        """Format meals from recent hours for specific time-based queries"""
        if not meals:
            return {
                'formatted_response': "You haven't logged any meals in the past 5 hours.",
                'meal_count': 0
            }
        
        response_text = f"In the past 5 hours, you've had {len(meals)} meal(s):\n\n"
        
        for meal in meals:
            time_str = meal.upload_time.strftime("%I:%M %p") if meal.upload_time else "Unknown time"
            meal_type = meal.meal_type or "Meal"
            
            # Get food items using proper extraction
            foods = self._extract_food_items(meal.analysis_data or {})
            foods_text = ', '.join(foods) if foods else 'Food items'
            
            # Get nutrition
            nutrition = meal.nutrition_summary or {}
            calories = nutrition.get('total_calories', 'Unknown')
            
            response_text += f"**{time_str}** ({meal_type}): {foods_text}"
            if calories != 'Unknown':
                response_text += f" - {calories} calories"
            response_text += "\n"
        
        return {
            'formatted_response': response_text,
            'meal_count': len(meals)
        }

    def _get_user_meal_history(self, user_id: int, days_back: int = 7) -> Dict[str, Any]:
        """Retrieve user's actual meal history from database"""
        try:
            from app.models.db_models import DailySummary, Meal

            # Get recent meals (last 7 days by default)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            recent_meals = self.db.query(Meal).filter(
                Meal.user_id == user_id,
                Meal.upload_date >= start_date,
                Meal.upload_date <= end_date
            ).order_by(Meal.upload_time.desc()).limit(20).all()
            
            # Get daily summaries for context
            daily_summaries = self.db.query(DailySummary).filter(
                DailySummary.user_id == user_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date
            ).order_by(DailySummary.date.desc()).all()
            
            # Process meal data
            processed_meals = []
            for meal in recent_meals:
                meal_data = {
                    'id': meal.id,
                    'meal_type': meal.meal_type,
                    'upload_date': meal.upload_date.isoformat() if meal.upload_date else None,
                    'upload_time': meal.upload_time.isoformat() if meal.upload_time else None,
                    'analysis_data': meal.analysis_data or {},
                    'nutrition_summary': meal.nutrition_summary or {},
                    'recommendations': meal.recommendations or {}
                }
                processed_meals.append(meal_data)
            
            # Process daily summaries
            processed_summaries = []
            for summary in daily_summaries:
                summary_data = {
                    'date': summary.date.isoformat(),
                    'total_calories': summary.total_calories,
                    'total_protein': summary.total_protein,
                    'total_carbs': summary.total_carbs,
                    'total_fat': summary.total_fat,
                    'total_fiber': summary.total_fiber,
                    'meals_count': summary.meals_count,
                    'goal_calories_achieved': summary.goal_calories_achieved,
                    'goal_protein_achieved': summary.goal_protein_achieved
                }
                processed_summaries.append(summary_data)
            
            return {
                'recent_meals': processed_meals,
                'daily_summaries': processed_summaries,
                'total_meals': len(processed_meals),
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            print(f"Error retrieving meal history: {e}")
            return {
                'recent_meals': [],
                'daily_summaries': [],
                'total_meals': 0,
                'error': str(e)
            }
    
    def _format_user_meal_history(self, meal_history: Dict[str, Any]) -> str:
        """Format user's actual meal history for the prompt"""
        try:
            if not meal_history or not meal_history.get('recent_meals'):
                return "No recent meal data available"
            
            recent_meals = meal_history['recent_meals'][:10]  # Last 10 meals
            daily_summaries = meal_history.get('daily_summaries', [])[:5]  # Last 5 days
            
            formatted_text = f"RECENT MEALS ({len(recent_meals)} meals):\n"
            
            for meal in recent_meals:
                meal_type = meal.get('meal_type', 'Unknown')
                upload_date = meal.get('upload_date', 'Unknown date')
                upload_time = meal.get('upload_time', '')
                
                # Format date and time together
                datetime_str = upload_date
                if upload_time:
                    try:
                        # Parse the ISO datetime string and format it nicely
                        from datetime import datetime
                        time_obj = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        time_formatted = time_obj.strftime("%I:%M %p")
                        datetime_str = f"{upload_date} at {time_formatted}"
                    except:
                        # Fallback if datetime parsing fails
                        datetime_str = f"{upload_date} (time: {upload_time})"
                
                # Get nutrition info
                nutrition = meal.get('nutrition_summary', {})
                calories = nutrition.get('total_calories', 'Unknown')
                protein = nutrition.get('total_protein', 'Unknown')
                
                # Get food items using proper extraction
                analysis_data = meal.get('analysis_data', {})
                foods = self._extract_food_items(analysis_data)
                foods_text = ', '.join(foods[:3]) if foods else 'Food items not analyzed'
                if len(foods) > 3:
                    foods_text += f' + {len(foods) - 3} more items'
                
                formatted_text += f"- {datetime_str} ({meal_type}): {foods_text} - {calories} cal, {protein}g protein\n"
            
            if daily_summaries:
                formatted_text += f"\nDAILY NUTRITION SUMMARIES:\n"
                for summary in daily_summaries:
                    date = summary.get('date', 'Unknown')
                    calories = summary.get('total_calories', 0)
                    protein = summary.get('total_protein', 0)
                    meals_count = summary.get('meals_count', 0)
                    formatted_text += f"- {date}: {calories:.0f} cal, {protein:.0f}g protein ({meals_count} meals)\n"
            
            return formatted_text
            
        except Exception as e:
            print(f"Error formatting meal history: {e}")
            return "Error retrieving meal history data"

    async def _generate_enhanced_response(
        self, 
        user_id: int, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced AI response using LangGraph agent with RAG."""
        try:
            # Use LangGraph agent (RAG retrieval happens inside the graph)
            result = await run_health_coach(
                user_id=user_id,
                message=message,
                session_id=context.get('session_id', 'unknown'),
                user_profile=context.get('user_profile', {}),
                user_meal_history=context.get('user_meal_history', {}),
                health_alerts=context.get('health_alerts', []),
            )

            return {
                'message': result.get('message', ''),
                'response_type': result.get('response_type', 'general'),
                'confidence': result.get('confidence', 0.9),
                'actions': result.get('actions', []),
                'trigger_notifications': result.get('trigger_notifications', False),
            }

        except Exception as e:
            print(f"[LangGraph] Error, falling back to direct Gemini: {e}")
            # Fallback to direct Gemini call
            try:
                prompt = self._build_enhanced_prompt(user_id, message, context)
                response = enhanced_agent_model.generate_content(prompt)
                response_text = response.text
                response_analysis = self._analyze_response(response_text, context)
                return {
                    'message': response_text,
                    'response_type': response_analysis.get('type', 'general'),
                    'confidence': response_analysis.get('confidence', 0.7),
                    'actions': response_analysis.get('actions', []),
                    'trigger_notifications': response_analysis.get('trigger_notifications', False),
                }
            except Exception as fallback_err:
                print(f"Fallback also failed: {fallback_err}")
                return {
                    'message': "I'm having trouble right now. Could you try again?",
                    'response_type': 'error',
                    'confidence': 0.3,
                    'actions': [],
                }
    
    def _build_enhanced_prompt(self, user_id: int, message: str, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt with all available context"""
        
        conversation_history = context.get('conversation_history', [])
        health_alerts = context.get('health_alerts', [])
        monitoring_insights = context.get('monitoring_insights', {})
        user_meal_history = context.get('user_meal_history', {})
        user_profile = context.get('user_profile', {})
        
        # Check for urgent health alerts
        urgent_alerts = [alert for alert in health_alerts if alert.get('severity') in ['high', 'critical']]
        
        # Format user's REAL meal data
        meal_history_text = self._format_user_meal_history(user_meal_history)
        user_profile_text = self._format_user_profile(user_profile)
        
        prompt = f"""
        You are a friendly, concise AI Health Coach with access to THIS USER'S ACTUAL health data and meal history.
        
        USER PROFILE & GOALS:
        {user_profile_text}
        
        USER'S ACTUAL MEAL HISTORY (Last 7 Days):
        {meal_history_text}
        
        CONVERSATION CONTEXT:
        {self._format_conversation_history(conversation_history)}
        
        HEALTH STATUS:
        {f"⚠️ URGENT: {len(urgent_alerts)} critical health alert(s) - address immediately!" if urgent_alerts else f"✅ {len(health_alerts)} active health insights available"}
        
        USER MESSAGE: {message}
        
        CRITICAL INSTRUCTIONS:
        1. **USE ACTUAL DATA**: Reference their REAL meals, nutrition data, and eating patterns from above
        2. **BE SPECIFIC**: Mention specific foods they ate, actual calorie/macro numbers when relevant
        3. **BE PERSONAL**: Use their name, reference their specific goals and preferences
        4. **BE CONCISE**: 2-3 sentences for simple questions, 4-5 for complex topics
        5. **BE ACTIONABLE**: Give specific suggestions based on their actual eating patterns
        6. **NO GENERIC RESPONSES**: Every response must be personalized to their actual data
        
        RESPONSE FORMAT:
        - Reference their actual meal data when relevant
        - Use specific numbers (calories, protein, etc.) from their history
        - Give personalized recommendations based on their real patterns
        - Keep responses concise and friendly
        
        EXAMPLE RESPONSES USING REAL DATA:
        "Looking at your meals from yesterday, you had 1,850 calories with good protein from that grilled chicken! Your fiber was a bit low though - try adding some vegetables to your next meal 🥕"
        
        "I see you've been consistent with breakfast this week - that's great! Your protein intake averages 85g daily, which is perfect for your goals. Keep it up! 💪"
        
        "⚠️ I notice you skipped lunch for 3 days this week. That 800-calorie dinner won't make up for it. Try setting a lunch reminder?"
        
        Remember: Use THEIR actual data, be specific, be helpful, be concise!
        """
        
        return prompt
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for prompt"""
        if not history:
            return "No previous conversation history"
        
        formatted = []
        for memory in history[-3:]:  # Last 3 exchanges
            formatted.append(f"- {memory['message_type'].title()}: {memory['content'][:100]}...")
        
        return "\n".join(formatted)
    
    def _format_user_profile(self, user_profile: Dict[str, Any]) -> str:
        """Format user profile information for the prompt"""
        try:
            if not user_profile or user_profile.get('error'):
                return "User profile not available"
            
            name = user_profile.get('name', 'User')
            daily_goals = user_profile.get('daily_goals', {})
            profile_data = user_profile.get('profile', {})
            
            formatted_text = f"USER: {name}\n"
            
            if daily_goals:
                formatted_text += "DAILY GOALS:\n"
                if daily_goals.get('calories'):
                    formatted_text += f"- Calories: {daily_goals['calories']}\n"
                if daily_goals.get('protein'):
                    formatted_text += f"- Protein: {daily_goals['protein']}g\n"
                if daily_goals.get('carbs'):
                    formatted_text += f"- Carbs: {daily_goals['carbs']}g\n"
                if daily_goals.get('fat'):
                    formatted_text += f"- Fat: {daily_goals['fat']}g\n"
            
            if profile_data:
                if profile_data.get('health_goals'):
                    formatted_text += f"HEALTH GOALS: {', '.join(profile_data['health_goals'])}\n"
                if profile_data.get('dietary_preferences'):
                    formatted_text += f"DIETARY PREFERENCES: {', '.join(profile_data['dietary_preferences'])}\n"
                if profile_data.get('allergies'):
                    formatted_text += f"ALLERGIES: {', '.join(profile_data['allergies'])}\n"
            
            return formatted_text
            
        except Exception as e:
            print(f"Error formatting user profile: {e}")
            return "Error retrieving user profile"

    def _get_user_profile_data(self, user_id: int) -> Dict[str, Any]:
        """Retrieve user's profile and goals from database"""
        try:
            from app.models.db_models import User
            
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {'error': 'User not found'}
            
            return {
                'user_id': user.id,
                'username': user.username,
                'name': user.name,
                'email': user.email,
                'profile': user.profile or {},
                'daily_goals': user.daily_goals or {},
                'notification_preferences': user.notification_preferences or {},
                'last_meal_time': user.last_meal_time.isoformat() if user.last_meal_time else None,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return {'error': str(e)}

    def _analyze_response(self, response_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the generated response for type, confidence, and actions"""
        
        response_lower = response_text.lower()
        analysis = {
            'type': 'general',
            'confidence': 0.8,
            'actions': [],
            'trigger_notifications': False
        }
        
        # Determine response type
        if any(word in response_lower for word in ['alert', 'concern', 'warning', 'urgent']):
            analysis['type'] = 'health_alert'
            analysis['confidence'] = 0.9
        elif any(word in response_lower for word in ['plan', 'schedule', 'meal planning']):
            analysis['type'] = 'meal_planning'
            analysis['trigger_notifications'] = True
        elif any(word in response_lower for word in ['goal', 'target', 'progress']):
            analysis['type'] = 'goal_tracking'
        elif any(word in response_lower for word in ['reminder', 'remember', 'don\'t forget']):
            analysis['type'] = 'reminder'
            analysis['trigger_notifications'] = True
        
        # Extract suggested actions
        if 'try' in response_lower or 'consider' in response_lower:
            analysis['actions'].append('dietary_adjustment')
        if 'track' in response_lower or 'log' in response_lower:
            analysis['actions'].append('meal_tracking')
        if 'plan' in response_lower:
            analysis['actions'].append('meal_planning')
        
        return analysis
    
    def _should_suggest_meal_planning(self, message: str, context: Dict[str, Any]) -> bool:
        """Determine if meal planning should be suggested"""
        message_lower = message.lower()
        
        # Suggest meal planning if user asks about planning or goals
        planning_keywords = ['plan', 'meal plan', 'what should i eat', 'help me plan', 'weekly meals']
        if any(keyword in message_lower for keyword in planning_keywords):
            return True
        
        # Suggest if user has goal-related queries
        goal_keywords = ['goal', 'target', 'lose weight', 'gain weight', 'healthy eating']
        if any(keyword in message_lower for keyword in goal_keywords):
            return True
        
        return False
    
    def _generate_meal_plan_suggestion(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Generate a meal plan suggestion"""
        try:
            # Check if user already has an active meal plan
            existing_plans = self.meal_planner.get_user_meal_plans(user_id, active_only=True)
            
            if existing_plans:
                return {
                    'type': 'existing_plan',
                    'message': 'You already have an active meal plan. Would you like to view it or create a new one?',
                    'existing_plan': existing_plans[0]
                }
            
            return {
                'type': 'new_plan_suggestion',
                'message': 'I can create a personalized meal plan for you based on your goals and preferences. Would you like me to generate one?',
                'benefits': [
                    'Personalized to your dietary preferences',
                    'Aligned with your health goals',
                    'Based on your eating patterns',
                    'Includes variety and nutrition balance'
                ]
            }
            
        except Exception as e:
            print(f"Error generating meal plan suggestion: {e}")
            return None
    
    def create_intelligent_meal_plan(self, user_id: int, plan_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an intelligent, personalized meal plan using LangGraph + RAG"""
        try:
            import asyncio
            prefs = plan_preferences or {}
            user_profile = self._get_user_profile_data(user_id)

            # Try LangGraph + RAG meal plan generation
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(
                            asyncio.run,
                            generate_langgraph_meal_plan(user_id, user_profile, prefs)
                        ).result()
                else:
                    result = asyncio.run(
                        generate_langgraph_meal_plan(user_id, user_profile, prefs)
                    )
                if not result.get('error'):
                    return result
                print(f"[LangGraph] Meal plan returned error, falling back: {result.get('error')}")
            except Exception as lg_err:
                print(f"[LangGraph] Meal plan failed, falling back: {lg_err}")

            # Fallback to direct Gemini
            return self._generate_gemini_meal_plan(user_id, prefs)

        except Exception as e:
            print(f"Error creating intelligent meal plan: {e}")
            return self._generate_gemini_meal_plan(user_id, plan_preferences or {})

    def _get_all_meal_items_for_plan(self, meal_plan_id: int, duration_days: int) -> list:
        """Fetch all meal plan items from the database"""
        try:
            if not meal_plan_id:
                return []
            from app.models.agentic_models import MealPlanItem
            items = self.db.query(MealPlanItem).filter(
                MealPlanItem.meal_plan_id == meal_plan_id
            ).order_by(MealPlanItem.day_of_plan, MealPlanItem.id).all()
            
            result = []
            for item in items:
                result.append({
                    'id': item.id,
                    'day_of_plan': item.day_of_plan,
                    'meal_type': item.meal_type,
                    'food_items': item.food_items if isinstance(item.food_items, list) else json.loads(item.food_items) if isinstance(item.food_items, str) else [],
                    'nutritional_info': item.nutritional_info if isinstance(item.nutritional_info, dict) else json.loads(item.nutritional_info) if isinstance(item.nutritional_info, str) else {},
                    'preparation_notes': item.preparation_notes,
                    'alternatives': item.alternatives if isinstance(item.alternatives, list) else json.loads(item.alternatives) if isinstance(item.alternatives, str) else [],
                })
            return result
        except Exception as e:
            print(f"Error fetching meal plan items: {e}")
            return []

    def _build_frontend_plan_from_items(self, meal_items: list, duration_days: int) -> Dict[str, Any]:
        """Build {days: [{day, meals: {breakfast: [...], ...}}]} from meal_items"""
        days_map = {}
        for item in meal_items:
            day_num = item.get('day_of_plan', 1)
            meal_type = item.get('meal_type', 'other')
            # Normalize meal type
            if 'snack' in meal_type.lower() or 'morning' in meal_type.lower():
                meal_type = 'snack'
            
            if day_num not in days_map:
                days_map[day_num] = {'day': f'Day {day_num}', 'meals': {}}
            
            if meal_type not in days_map[day_num]['meals']:
                days_map[day_num]['meals'][meal_type] = []
            
            food_items = item.get('food_items', [])
            for food in food_items:
                days_map[day_num]['meals'][meal_type].append({
                    'name': food.get('name', 'Unknown'),
                    'calories': food.get('calories'),
                    'protein': food.get('protein'),
                    'quantity': food.get('quantity'),
                })
        
        # Sort by day number and build array
        days = [days_map[d] for d in sorted(days_map.keys())]
        
        # If no items found, return empty structure
        if not days:
            days = [{'day': f'Day {i+1}', 'meals': {}} for i in range(duration_days)]
        
        return {'days': days}

    def _generate_gemini_meal_plan(self, user_id: int, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Generate meal plan directly via a single Gemini AI call"""
        import time
        try:
            user_profile = self._get_user_profile_data(user_id)
            goals = prefs.get('goals', {}) or {}
            duration = prefs.get('duration_days', 7)

            prompt = f"""You are a nutrition expert. Generate a {duration}-day meal plan.

User Profile: {json.dumps(user_profile.get('profile', {}))}
Daily Goals: {json.dumps(user_profile.get('daily_goals', {}))}
Preferences: {json.dumps(goals)}

Return a JSON object with this EXACT structure:
{{
  "days": [
    {{
      "day": "Day 1",
      "meals": {{
        "breakfast": [{{"name": "food item with quantity", "calories": 300}}],
        "lunch": [{{"name": "food item with quantity", "calories": 500}}],
        "dinner": [{{"name": "food item with quantity", "calories": 400}}],
        "snack": [{{"name": "food item with quantity", "calories": 150}}]
      }}
    }}
  ]
}}

IMPORTANT:
- Include Indian cuisine where appropriate
- Match dietary restrictions: {goals.get('dietary_restrictions', 'none')}
- Target ~{goals.get('calorie_target', 2000)} calories/day
- Cuisine preference: {goals.get('cuisine_preference', 'any')}
- Include 2-3 food items per meal for variety
- Return ONLY valid JSON, no markdown or extra text"""

            # Retry with backoff for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = enhanced_agent_model.generate_content(prompt)
                    response_text = response.text
                    break
                except Exception as api_error:
                    if '429' in str(api_error) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 30  # 30s, 60s
                        print(f"Rate limited on meal plan generation, waiting {wait_time}s (attempt {attempt + 1})")
                        time.sleep(wait_time)
                    else:
                        raise

            # Parse JSON from the response
            import re
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            response_text = response_text.strip()

            plan_data = json.loads(response_text)

            return {
                'meal_plan': plan_data,
                'plan_type': prefs.get('plan_type', 'weekly'),
                'duration_days': duration,
                'generation_method': 'gemini_direct'
            }

        except Exception as e:
            print(f"Error in Gemini meal plan fallback: {e}")
            return {'error': f'Failed to generate meal plan: {str(e)}'}

    def _convert_plan_to_frontend_format(self, plan_data: Dict[str, Any], duration_days: int) -> Dict[str, Any]:
        """Convert internal plan data structure to frontend-expected format with 'days' array"""
        try:
            days = []
            if isinstance(plan_data, dict):
                # If plan_data already has a list structure, transform it
                for day_num in range(1, duration_days + 1):
                    day_key = f'day_{day_num}'
                    day_data = plan_data.get(day_key, plan_data.get(str(day_num), {}))
                    if isinstance(day_data, dict):
                        meals = {}
                        for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
                            meal_items = day_data.get(meal_type, [])
                            if isinstance(meal_items, list):
                                meals[meal_type] = meal_items
                            elif isinstance(meal_items, str):
                                meals[meal_type] = [{'name': meal_items}]
                        if meals:
                            days.append({'day': f'Day {day_num}', 'meals': meals})

            if not days:
                # Return the original data as-is with a wrapper
                return plan_data

            return {'days': days}

        except Exception as e:
            print(f"Error converting plan format: {e}")
            return plan_data

    def get_user_health_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive health dashboard with all agentic insights"""
        try:
            # Get conversation summary
            conversation_summary = self.conversation_memory.get_user_conversation_summary(user_id)
            
            # Get active alerts
            active_alerts = self.health_monitor.get_active_alerts(user_id)
            
            # Get pending notifications
            pending_notifications = self.notification_service.get_pending_notifications(user_id)
            
            # Get meal plans
            meal_plans = self.meal_planner.get_user_meal_plans(user_id, active_only=True)
            
            # Run health monitoring for latest insights
            monitoring_results = self.health_monitor.run_health_monitoring(user_id)
            
            return {
                'user_id': user_id,
                'dashboard_generated_at': datetime.now().isoformat(),
                'conversation_insights': {
                    'total_conversations': conversation_summary.get('total_conversations', 0),
                    'engagement_score': conversation_summary.get('avg_importance_score', 0),
                    'common_topics': conversation_summary.get('common_topics', {}),
                    'last_conversation': conversation_summary.get('last_conversation')
                },
                'health_monitoring': {
                    'active_alerts': len(active_alerts),
                    'urgent_alerts': len([a for a in active_alerts if a['severity'] in ['high', 'critical']]),
                    'recent_insights': monitoring_results.get('insights_generated', 0),
                    'patterns_updated': monitoring_results.get('patterns_updated', 0)
                },
                'smart_notifications': {
                    'pending_notifications': len(pending_notifications),
                    'next_notification': pending_notifications[0] if pending_notifications else None
                },
                'meal_planning': {
                    'active_plans': len(meal_plans),
                    'current_plan': meal_plans[0] if meal_plans else None,
                    'adherence_score': meal_plans[0]['adherence_score'] if meal_plans else 0
                },
                'alerts': active_alerts[:5],  # Top 5 alerts
                'recent_meals': self._get_user_meal_history(user_id, days_back=3)
            }
            
        except Exception as e:
            print(f"Error generating health dashboard: {e}")
            return {'error': str(e)}

    def get_conversation_insights(self, user_id: int) -> Dict[str, Any]:
        """Get detailed conversation insights and patterns for a user"""
        try:
            # Get conversation summary from memory service
            conversation_summary = self.conversation_memory.get_user_conversation_summary(user_id)
            
            # Get contextual memory for topic analysis
            recent_memory = self.conversation_memory.get_contextual_memory(user_id, limit=50)
            
            # Analyze common topics from recent conversations
            topics = {}
            for memory in recent_memory:
                content = memory.get('content', '') if isinstance(memory, dict) else str(memory)
                for topic in ['breakfast', 'lunch', 'dinner', 'snack', 'protein', 'calories', 
                              'weight', 'exercise', 'diet', 'meal plan', 'nutrition']:
                    if topic in content.lower():
                        topics[topic] = topics.get(topic, 0) + 1
            
            return {
                'user_id': user_id,
                'total_conversations': conversation_summary.get('total_conversations', 0),
                'engagement_score': conversation_summary.get('avg_importance_score', 0),
                'common_topics': topics,
                'last_conversation': conversation_summary.get('last_conversation'),
                'conversation_frequency': conversation_summary.get('conversation_frequency', 'unknown'),
                'important_memories': conversation_summary.get('important_memories', []),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting conversation insights: {e}")
            return {'error': str(e)}

    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old data across all agentic services"""
        try:
            from app.models.agentic_models import (
                ConversationMemory, HealthAlert, SmartNotification, PredictiveInsight
            )
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned = {}
            
            # Clean old conversation memories (keep important ones)
            old_memories = self.db.query(ConversationMemory).filter(
                ConversationMemory.created_at < cutoff_date,
                ConversationMemory.importance_score < 0.5
            ).count()
            self.db.query(ConversationMemory).filter(
                ConversationMemory.created_at < cutoff_date,
                ConversationMemory.importance_score < 0.5
            ).delete()
            cleaned['conversation_memories'] = old_memories
            
            # Clean dismissed/expired health alerts
            old_alerts = self.db.query(HealthAlert).filter(
                HealthAlert.triggered_at < cutoff_date,
                HealthAlert.is_dismissed == True
            ).count()
            self.db.query(HealthAlert).filter(
                HealthAlert.triggered_at < cutoff_date,
                HealthAlert.is_dismissed == True
            ).delete()
            cleaned['health_alerts'] = old_alerts
            
            # Clean sent notifications
            old_notifs = self.db.query(SmartNotification).filter(
                SmartNotification.created_at < cutoff_date,
                SmartNotification.is_sent == True
            ).count()
            self.db.query(SmartNotification).filter(
                SmartNotification.created_at < cutoff_date,
                SmartNotification.is_sent == True
            ).delete()
            cleaned['smart_notifications'] = old_notifs
            
            # Clean expired predictive insights
            old_insights = self.db.query(PredictiveInsight).filter(
                PredictiveInsight.created_at < cutoff_date,
                PredictiveInsight.is_active == False
            ).count()
            self.db.query(PredictiveInsight).filter(
                PredictiveInsight.created_at < cutoff_date,
                PredictiveInsight.is_active == False
            ).delete()
            cleaned['predictive_insights'] = old_insights
            
            self.db.commit()
            
            total_cleaned = sum(cleaned.values())
            print(f"Cleanup completed: {total_cleaned} records removed")
            
            return {
                'success': True,
                'total_cleaned': total_cleaned,
                'details': cleaned,
                'cutoff_date': cutoff_date.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            print(f"Error during cleanup: {e}")
            return {'error': str(e)}

    def _format_targeted_meal_response(self, meals: List, summaries: List, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format meal data based on specific user query with proper time display"""
        timeframe = query_info['timeframe']
        specific_request = query_info.get('specific_request')
        
        if not meals:
            return {
                'formatted_response': f"No meals found for {timeframe}.",
                'meal_count': 0
            }
        
        response_text = ""
        
        if timeframe == 'today':
            response_text = f"Today you've had {len(meals)} meal(s):\n\n"
        elif timeframe == 'yesterday':
            response_text = f"Yesterday you had {len(meals)} meal(s):\n\n"
        elif timeframe == 'week':
            response_text = f"This week you've had {len(meals)} meal(s):\n\n"
        else:
            response_text = f"Recently you've had {len(meals)} meal(s):\n\n"
        
        # Add specific nutrition focus if requested
        if specific_request == 'calories':
            total_calories = sum([
                meal.nutrition_summary.get('total_calories', 0) 
                for meal in meals 
                if meal.nutrition_summary
            ])
            response_text += f"**Total Calories: {total_calories:.0f}**\n\n"
        elif specific_request == 'protein':
            total_protein = sum([
                meal.nutrition_summary.get('total_protein', 0) 
                for meal in meals 
                if meal.nutrition_summary
            ])
            response_text += f"**Total Protein: {total_protein:.0f}g**\n\n"
        
        # List meals with proper time formatting
        for meal in meals[:10]:  # Show up to 10 meals
            date_str = meal.upload_date.strftime("%m/%d") if meal.upload_date else "Unknown"
            time_str = meal.upload_time.strftime("%I:%M %p") if meal.upload_time else "Unknown time"
            meal_type = meal.meal_type or "Meal"
            
            # Get food items using proper extraction
            foods = self._extract_food_items(meal.analysis_data or {})
            foods_text = ', '.join(foods[:3]) if foods else 'Food items'
            if len(foods) > 3:
                foods_text += f" + {len(foods) - 3} more"
            
            # Get nutrition
            nutrition = meal.nutrition_summary or {}
            calories = nutrition.get('total_calories', 0)
            protein = nutrition.get('total_protein', 0)
            
            response_text += f"• **{date_str} at {time_str}** ({meal_type}): {foods_text}"
            if calories > 0:
                response_text += f" - {calories:.0f} cal"
            if protein > 0:
                response_text += f", {protein:.0f}g protein"
            response_text += "\n"
        
        return {
            'formatted_response': response_text,
            'meal_count': len(meals)
        }