import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from app.config import settings
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.health_monitoring_service import HealthMonitoringService
from app.services.intelligent_meal_planner import IntelligentMealPlanner
from app.services.smart_notification_service import SmartNotificationService
from sqlalchemy.orm import Session

# Configure Gemini AI
genai.configure(api_key=settings.google_api_key)
enhanced_agent_model = genai.GenerativeModel("models/gemini-2.0-flash")

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
            
            # Enhance message context for vague inputs
            enhanced_context = self._enhance_message_context(message, enhanced_context)
            
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
            
            # Even on error, provide personalized response based on available context
            try:
                user_profile_data = self._get_user_profile_data(user_id)
                profile_data = user_profile_data.get('profile', {})
                goal = profile_data.get('goal', 'your health goals')
                diet_preference = profile_data.get('diet_preference', 'your dietary preferences')
                
                personalized_error = f"I'm experiencing a technical hiccup, but I'm still here to help with your {goal.lower()}! I can assist with nutrition advice, meal planning for your {diet_preference.lower()} diet, and tracking your progress. What would you like to know?"
                
                return {
                    'message': personalized_error,
                    'response_type': 'personalized_error_recovery',
                    'session_id': session_id or 'unknown',
                    'confidence': 0.7,
                    'contextual_insights': {'error_handled_with_personalization': True},
                    'timestamp': datetime.now().isoformat()
                }
            except:
                # Absolute last resort - still try to be helpful
                return {
                    'message': "I'm having a brief technical issue, but I'm here to help with your nutrition and health goals! Please try your question again.",
                    'response_type': 'error',
                    'session_id': session_id or 'unknown',
                    'confidence': 0.5,
                    'timestamp': datetime.now().isoformat()
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

    def _enhance_message_context(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context for vague messages to ensure personalized responses"""
        message_lower = message.lower().strip()
        
        # Detect vague messages that need personalized enhancement
        vague_patterns = [
            '.', '..', '...', 'hi', 'hello', 'hey', 'yo', 'sup', 'hii', 'hiii',
            'h', 'ok', 'k', 'hmm', 'uhm', 'um', 'yes', 'no', 'y', 'n',
            'good', 'bad', 'fine', 'ok then', 'alright', 'sure', 'whatever'
        ]
        
        is_vague_message = (
            message_lower in vague_patterns or 
            len(message.strip()) <= 3 or
            message.count('.') >= len(message.strip()) / 2
        )
        
        if is_vague_message:
            # Add special context for vague messages
            context['message_type'] = 'vague_input'
            context['requires_personalized_checkin'] = True
            
            # Add profile emphasis for personalization
            user_profile = context.get('user_profile', {})
            profile_data = user_profile.get('profile', {})
            
            context['personalization_emphasis'] = {
                'gender': profile_data.get('gender', ''),
                'diet_preference': profile_data.get('diet_preference', ''),
                'goal': profile_data.get('goal', ''),
                'activity': profile_data.get('activity', ''),
                'should_provide_checkin': True
            }
        
        return context

    async def _generate_enhanced_response(
        self, 
        user_id: int, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced AI response using all available context"""
        
        # Build comprehensive prompt with all context
        prompt = self._build_enhanced_prompt(user_id, message, context)
        
        # Always use Gemini - retry with simplified prompt if needed
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Generate response using Gemini AI
                if attempt == 0:
                    # First attempt: Use full enhanced prompt
                    response = enhanced_agent_model.generate_content(prompt)
                else:
                    # Retry attempts: Use simplified prompt for reliability
                    simplified_prompt = self._build_simplified_prompt(user_id, message, context)
                    print(f"Retry attempt {attempt} with simplified prompt")
                    response = enhanced_agent_model.generate_content(simplified_prompt)
                
                response_text = response.text.strip()
                
                # Validate response is not empty
                if not response_text:
                    if attempt < max_retries - 1:
                        continue  # Retry
                    else:
                        response_text = f"I'm here to help with your nutrition goals! Based on your profile, I can provide personalized advice. What would you like to know about your diet or health?"
                
                # Analyze response for actions and insights
                response_analysis = self._analyze_response(response_text, context)
                
                return {
                    'message': response_text,
                    'response_type': response_analysis.get('type', 'general'),
                    'confidence': response_analysis.get('confidence', 0.8),
                    'actions': response_analysis.get('actions', []),
                    'trigger_notifications': response_analysis.get('trigger_notifications', False)
                }
                
            except Exception as e:
                print(f"Gemini error attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    # Final fallback - still personalized based on user profile
                    user_profile = context.get('user_profile', {})
                    profile_data = user_profile.get('profile', {})
                    goal = profile_data.get('goal', 'your health goals')
                    
                    personalized_fallback = f"I'm having a brief technical issue, but I'm here to help with your {goal.lower()}! Please try asking your question again, and I'll provide personalized nutrition advice based on your profile."
                    
                    return {
                        'message': personalized_fallback,
                        'response_type': 'technical_issue',
                        'confidence': 0.5,
                        'actions': []
                    }
                continue  # Retry on error
    
    def _build_simplified_prompt(self, user_id: int, message: str, context: Dict[str, Any]) -> str:
        """Build simplified prompt for retry attempts"""
        user_profile = context.get('user_profile', {})
        profile_data = user_profile.get('profile', {})
        
        # Essential profile data only
        gender = profile_data.get('gender', '')
        diet_preference = profile_data.get('diet_preference', '')
        goal = profile_data.get('goal', '')
        activity = profile_data.get('activity', '')
        
        is_vague_input = context.get('requires_personalized_checkin', False)
        
        prompt = f"""You are a friendly AI Health Coach. Answer the user's question accurately and helpfully.

USER PROFILE: {gender} | {diet_preference} diet | Goal: {goal} | Activity: {activity}

USER MESSAGE: {message}

INSTRUCTIONS:
- If asking about profile: Answer with their specific profile info above
- If asking general nutrition: Provide accurate nutrition information
- If vague message: Give personalized check-in based on their {goal} goal and {diet_preference} diet
- Always be concise (2-3 sentences) and reference their profile when relevant

Answer their actual question directly and helpfully."""
        
        return prompt

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
        
        # Check if this is a vague message requiring personalized check-in
        is_vague_input = context.get('requires_personalized_checkin', False)
        personalization_data = context.get('personalization_emphasis', {})
        
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
        
        {f'''
        🎯 SPECIAL INSTRUCTION - VAGUE MESSAGE DETECTED:
        The user sent a vague/unclear message. Provide a PERSONALIZED check-in based on their profile:
        - Gender: {personalization_data.get('gender', 'Not specified')}
        - Diet: {personalization_data.get('diet_preference', 'Not specified')}
        - Goal: {personalization_data.get('goal', 'Not specified')}
        - Activity: {personalization_data.get('activity', 'Not specified')}
        
        Give them a friendly, personalized greeting that:
        1. References their specific goal and diet preference
        2. Mentions something from their recent meal history
        3. Asks about their current nutrition needs
        4. Offers relevant suggestions based on their profile
        
        Example: "Hey! How's your [goal] journey going? I see you're following a [diet] approach - have you had enough protein today for your muscle building? Your last meal was [specific meal] at [time]. Need any [diet-appropriate] meal suggestions? 💪"
        ''' if is_vague_input else ''}
        
        CRITICAL INSTRUCTIONS:
        
        🎯 **QUESTION TYPE DETECTION** - Answer appropriately based on what user is asking:
        
        **PROFILE QUESTIONS** (e.g., "what are my dietary preferences", "what's my goal"):
        - Answer directly from their profile data above
        - Be clear and specific: "Your dietary preference is Eggetarian and your goal is Build Muscle"
        
        **GENERAL NUTRITION QUESTIONS** (e.g., "how many calories in apple", "what vitamins are in spinach"):
        - Provide accurate general nutrition information
        - Reference their profile when relevant (e.g., "For your muscle building goal, apples provide...")
        
        **MEAL HISTORY QUESTIONS** (e.g., "what did I eat", "my recent meals"):
        - Use their actual meal data from above
        - Be specific about foods, calories, and timing
        
        **PERSONALIZED ADVICE REQUESTS** (e.g., "what should I eat", "meal suggestions"):
        - Combine their profile + meal history + general nutrition knowledge
        - Give specific, actionable recommendations
        
        **VAGUE MESSAGES** (e.g., "..", "hi", "hello"):
        - Provide personalized check-in based on their profile
        
        **CORE RULES**:
        1. **ANSWER THE ACTUAL QUESTION** - Don't force meal history into every response
        2. **BE ACCURATE** - Use correct nutrition information for general questions
        3. **BE PERSONAL** - Reference their profile when relevant
        4. **BE CONCISE** - 2-3 sentences for simple questions
        5. **BE HELPFUL** - Focus on what they actually asked
        
        EXAMPLE RESPONSES BY QUESTION TYPE:
        
        **Profile Questions:**
        Q: "what are my dietary preferences and goal"
        A: "Your dietary preference is Eggetarian (vegetarian + eggs) and your goal is Build Muscle. You're also Moderately Active, which means you need adequate protein for muscle growth!"
        
        **General Nutrition Questions:**
        Q: "how many calories in an apple"
        A: "A medium apple has about 95 calories and 4g fiber. For your muscle building goal, pair it with some nuts or yogurt for added protein! 🍎"
        
        **Meal History Questions:**
        Q: "what did I eat today"
        A: "Today at 12:34 PM you had Chicken Biryani (1 small plate, 200g) with 410 calories and 24g protein - great protein choice for muscle building!"
        
        **Personalized Advice:**
        Q: "what should I eat for dinner"
        A: "For your Eggetarian muscle building goals, try paneer curry with quinoa, or a veggie omelet with whole grain toast. Aim for 25-30g protein! 💪"
        
        **Vague Messages:**
        Q: ".." or "hi"
        A: "Hey! How's your muscle building journey going? I see you're following an Eggetarian diet - have you hit your protein target today? Need any meal suggestions? 🥚💪"
        
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
            
            # CRITICAL: Extract Dashboard personalization settings
            if profile_data:
                # Core personalization settings from Dashboard
                gender = profile_data.get('gender', '')
                diet_preference = profile_data.get('diet_preference', '')
                goal = profile_data.get('goal', '')
                activity = profile_data.get('activity', '')
                
                if gender or diet_preference or goal or activity:
                    formatted_text += "PERSONALIZATION PROFILE:\n"
                    if gender:
                        formatted_text += f"- Gender: {gender}\n"
                    if diet_preference:
                        formatted_text += f"- Diet Preference: {diet_preference}\n"
                    if goal:
                        formatted_text += f"- Primary Goal: {goal}\n"
                    if activity:
                        formatted_text += f"- Activity Level: {activity}\n"
                
                # Legacy profile fields
                if profile_data.get('health_goals'):
                    formatted_text += f"- Additional Health Goals: {', '.join(profile_data['health_goals'])}\n"
                if profile_data.get('dietary_preferences'):
                    formatted_text += f"- Additional Dietary Preferences: {', '.join(profile_data['dietary_preferences'])}\n"
                if profile_data.get('allergies'):
                    formatted_text += f"- Allergies: {', '.join(profile_data['allergies'])}\n"
            
            if daily_goals:
                formatted_text += "DAILY NUTRITION GOALS:\n"
                if daily_goals.get('calories'):
                    formatted_text += f"- Calories: {daily_goals['calories']}\n"
                if daily_goals.get('protein'):
                    formatted_text += f"- Protein: {daily_goals['protein']}g\n"
                if daily_goals.get('carbs'):
                    formatted_text += f"- Carbs: {daily_goals['carbs']}g\n"
                if daily_goals.get('fat'):
                    formatted_text += f"- Fat: {daily_goals['fat']}g\n"
            
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
    
    # Additional helper methods for completeness...
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