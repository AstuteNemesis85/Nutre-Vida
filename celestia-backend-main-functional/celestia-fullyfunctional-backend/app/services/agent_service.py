import json
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from sqlalchemy.orm import Session
from app.config import settings
from app.services.user_service import get_meal_history, get_user
from datetime import datetime, timedelta

genai.configure(api_key=settings.google_api_key)
agent_model = genai.GenerativeModel("models/gemini-2.0-flash")

class HealthCoachAgent:
    def __init__(self, db: Session = None):
        self.db = db
        self.system_prompt = """
        You are an AI Health Coach specializing in Indian nutrition and wellness. Your responses should be:
        
        RESPONSE STYLE:
        - CONCISE: Keep responses to 2-3 sentences max unless asked for details
        - CONVERSATIONAL: Use natural, friendly dialogue like talking to a friend
        - ACTIONABLE: Always include one specific, doable suggestion
        - POSITIVE: Focus on what they CAN do, not restrictions
        - PERSONAL: Reference their specific food choices and goals when possible
        
        PERSONALITY:
        - Warm, encouraging friend who happens to know nutrition
        - Never preachy or judgmental about food choices
        - Celebrates small wins and progress over perfection
        - Uses simple language, avoids medical jargon
        - Understands Indian food culture and family dynamics
        
        INDIAN NUTRITION EXPERTISE:
        - Deep knowledge of Indian cuisine, regional dishes, spices
        - Understanding of vegetarian nutrition and protein combining
        - Familiarity with Indian meal patterns and festival foods
        - Knowledge of Ayurvedic principles and traditional remedies
        - Awareness of common challenges (iron deficiency, diabetes)
        
        RESPONSE FORMAT:
        - Start with acknowledgment of their input
        - Give ONE key insight or suggestion
        - End with encouragement or next step
        - Use emojis sparingly (max 1-2 per response)
        
        Example good response: "Great choice with the dal and rice combo! That's complete protein right there. Try adding some spinach next time for extra iron. You're building really healthy habits! 💪"
        
        Example bad response: Long paragraphs explaining protein science, multiple suggestions, medical terminology.
        """
    
    def get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Retrieve user's profile and recent meal history with calendar data"""
        if not self.db or not user_id:
            return {}
        
        user = get_user(self.db, user_id)
        if not user:
            return {}
        
        # Get meal history with calendar information
        from app.services.dashboard_service import DashboardService
        dashboard_service = DashboardService(self.db)
        
        # Get recent meals with calendar data
        meal_history = dashboard_service.get_meal_history_with_calendar(user_id, 30)
        
        # Get today's dashboard data
        today_data = dashboard_service.get_daily_dashboard(user_id)
        
        # Calculate weekly stats
        meals = get_meal_history(self.db, user_id)
        weekly_stats = self.calculate_weekly_stats(meals[:7])
        
        # Add calendar-aware insights
        calendar_insights = self.get_calendar_insights(meal_history)
        
        return {
            "profile": user.profile,
            "daily_goals": user.daily_goals or {},
            "recent_meals": len(meal_history),
            "weekly_stats": weekly_stats,
            "today_data": today_data,
            "calendar_insights": calendar_insights,
            "goals": user.profile.get("health_goals", []),
            "allergies": user.profile.get("allergies", []),
            "diet_preference": user.profile.get("diet_preference", "none"),
            "meal_history": meal_history[:10]  # Last 10 meals for context
        }
    
    def calculate_weekly_stats(self, meals: List) -> Dict[str, Any]:
        """Calculate nutritional statistics from meal history"""
        if not meals:
            return {}
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        meal_count = 0
        
        for meal in meals:
            if meal.analysis_data:
                total_calories += meal.analysis_data.get("total_calories", 0)
                total_protein += meal.analysis_data.get("total_protein", 0)
                total_carbs += meal.analysis_data.get("total_carbs", 0)
                total_fat += meal.analysis_data.get("total_fat", 0)
                meal_count += 1
        
        if meal_count == 0:
            return {}
        
        return {
            "avg_daily_calories": round(total_calories / min(7, meal_count)),
            "avg_daily_protein": round(total_protein / min(7, meal_count)),
            "avg_daily_carbs": round(total_carbs / min(7, meal_count)),
            "avg_daily_fat": round(total_fat / min(7, meal_count)),
            "meals_tracked": meal_count
        }
    
    def analyze_nutritional_gaps(self, current_analysis: Dict, user_context: Dict) -> List[str]:
        """Identify nutritional gaps and areas for improvement with Indian context"""
        insights = []
        
        # Check protein intake with Indian context
        if current_analysis.get("total_protein", 0) < 15:
            diet_pref = user_context.get("diet_preference", "")
            if diet_pref == "vegetarian":
                insights.append("Your meal is low in protein. Consider adding dal, paneer, curd, or combining rice with lentils for complete protein.")
            else:
                insights.append("Your meal is low in protein. Consider adding chicken, fish, eggs, dal, or paneer.")
        
        # Check for traditional Indian vegetables and fiber
        has_vegetables = any(any(veg in item.get("name", "").lower() for veg in 
                               ["vegetable", "sabzi", "curry", "dal", "sambar", "rasam", "salad"]) 
                            for item in current_analysis.get("items", []))
        if not has_vegetables:
            insights.append("Try adding traditional Indian vegetables like palak, bhindi, or seasonal sabzi for fiber and micronutrients.")
        
        # Check calorie density with Indian meal context
        total_calories = current_analysis.get("total_calories", 0)
        if total_calories > 800:
            insights.append("This is a calorie-dense meal. Consider smaller portions of rice/roti or use less ghee/oil if weight management is your goal.")
        
        # Indian diet-specific recommendations
        diet_pref = user_context.get("diet_preference", "")
        if diet_pref == "vegetarian":
            non_veg_items = [item for item in current_analysis.get("items", []) 
                           if not item.get("is_vegetarian", True)]
            if non_veg_items:
                insights.append(f"Note: {', '.join([item['name'] for item in non_veg_items])} may not align with your vegetarian preference.")
        
        # Check for iron-rich foods (common deficiency in India)
        iron_rich_foods = ["spinach", "palak", "methi", "bajra", "ragi", "jaggery", "gud"]
        has_iron_rich = any(any(food in item.get("name", "").lower() for food in iron_rich_foods) 
                           for item in current_analysis.get("items", []))
        if not has_iron_rich and diet_pref == "vegetarian":
            insights.append("Consider adding iron-rich foods like palak, methi, or jaggery, especially with vitamin C sources like lemon.")
        
        return insights
    
    def get_calendar_insights(self, meal_history: List[Dict]) -> Dict[str, Any]:
        """Generate insights based on calendar patterns"""
        if not meal_history:
            return {}
        
        # Analyze eating patterns by day of week
        day_patterns = {}
        meal_type_patterns = {}
        
        for meal in meal_history:
            day = meal.get("day_of_week", "Unknown")
            meal_type = meal.get("meal_type", "unknown")
            
            if day not in day_patterns:
                day_patterns[day] = {"count": 0, "calories": 0}
            if meal_type not in meal_type_patterns:
                meal_type_patterns[meal_type] = {"count": 0, "calories": 0}
            
            day_patterns[day]["count"] += 1
            meal_type_patterns[meal_type]["count"] += 1
            
            if meal.get("analysis_data"):
                calories = meal["analysis_data"].get("total_calories", 0)
                day_patterns[day]["calories"] += calories
                meal_type_patterns[meal_type]["calories"] += calories
        
        return {
            "day_patterns": day_patterns,
            "meal_type_patterns": meal_type_patterns,
            "total_days_tracked": len(set(meal.get("upload_date") for meal in meal_history if meal.get("upload_date")))
        }
    
    def generate_motivational_message(self, user_context: Dict) -> str:
        """Generate personalized motivational message with calendar awareness"""
        meals_tracked = user_context.get("weekly_stats", {}).get("meals_tracked", 0)
        today_data = user_context.get("today_data", {})
        calendar_insights = user_context.get("calendar_insights", {})
        
        # Check today's progress
        if today_data.get("meals_count", 0) > 0:
            if today_data.get("goal_calories_achieved"):
                return f"Fantastic! You've hit your calorie goal today with {today_data['meals_count']} meals tracked. Keep up the great work! 🎯"
            else:
                remaining_calories = today_data.get("goals", {}).get("calories", 2000) - today_data.get("total_calories", 0)
                if remaining_calories > 0:
                    return f"You're doing great today! {remaining_calories} calories left to reach your goal. You've got this! 💪"
        
        # Weekly patterns
        if meals_tracked == 0:
            return "Welcome! Let's start your health journey together. Every meal tracked is a step toward your goals!"
        elif meals_tracked < 3:
            return "Great start! You're building healthy habits. Keep tracking to see patterns emerge."
        elif meals_tracked < 7:
            return f"Awesome! You've tracked {meals_tracked} meals this week. Consistency is key to success!"
        else:
            # Check for streaks
            total_days = calendar_insights.get("total_days_tracked", 0)
            if total_days >= 7:
                return f"Outstanding! {total_days} days of consistent tracking. You're building a strong healthy routine! 🌟"
            else:
                return f"Great commitment! {meals_tracked} meals tracked. You're well on your way to achieving your health goals!"
    
    def suggest_meal_improvements(self, current_analysis: Dict) -> List[Dict[str, str]]:
        """Suggest specific improvements for the current meal with Indian context"""
        suggestions = []
        
        # Analyze macronutrient balance
        total_calories = current_analysis.get("total_calories", 1)
        protein_percent = (current_analysis.get("total_protein", 0) * 4 / total_calories) * 100 if total_calories > 0 else 0
        carbs_percent = (current_analysis.get("total_carbs", 0) * 4 / total_calories) * 100 if total_calories > 0 else 0
        fat_percent = (current_analysis.get("total_fat", 0) * 9 / total_calories) * 100 if total_calories > 0 else 0
        
        if protein_percent < 20:
            suggestions.append({
                "type": "protein",
                "suggestion": "Add Indian protein sources like dal, paneer, curd, or combine rice with rajma/chana",
                "benefit": "Helps with satiety and muscle maintenance, traditional Indian way"
            })
        
        if carbs_percent > 60:
            suggestions.append({
                "type": "carbs",
                "suggestion": "Replace white rice with brown rice, or add more vegetables to reduce carb proportion",
                "benefit": "Better blood sugar control and sustained energy, important for Indian meals"
            })
        
        if fat_percent < 20:
            suggestions.append({
                "type": "healthy_fats",
                "suggestion": "Add healthy fats like ghee (in moderation), nuts, seeds, or coconut",
                "benefit": "Improves nutrient absorption and satisfaction, traditional Indian approach"
            })
        
        # Indian-specific suggestions
        has_spices = any(any(spice in item.get("name", "").lower() for spice in 
                           ["turmeric", "haldi", "ginger", "adrak", "garlic", "lehsun"]) 
                        for item in current_analysis.get("items", []))
        if not has_spices:
            suggestions.append({
                "type": "spices",
                "suggestion": "Add traditional Indian spices like turmeric, ginger, or garlic for health benefits",
                "benefit": "Anti-inflammatory properties and better digestion"
            })
        
        return suggestions
    
    async def chat(self, message: str, context: Dict[str, Any]) -> str:
        """Main chat function for the AI agent with meal memory capabilities"""
        try:
            # Build context-aware prompt
            user_context = {}
            meal_memory_result = None
            
            if context.get("user_id") and self.db:
                user_context = self.get_user_context(context["user_id"])
                
                # Check if this is a meal memory query
                meal_memory_result = self.handle_meal_memory_query(context["user_id"], message)
            
            current_analysis = context.get("current_analysis", {})
            chat_history = context.get("chat_history", [])
            
            # If meal memory found a specific answer, return it
            if meal_memory_result and meal_memory_result.get('result'):
                return meal_memory_result['result']
            
            # Get insights
            nutritional_gaps = []
            meal_improvements = []
            if current_analysis:
                nutritional_gaps = self.analyze_nutritional_gaps(current_analysis, user_context)
                meal_improvements = self.suggest_meal_improvements(current_analysis)
            
            # Build the prompt
            prompt = f"""
            {self.system_prompt}
            
            Current Context:
            - User Profile: {json.dumps(user_context.get('profile', {}), indent=2)}
            - Daily Goals: {json.dumps(user_context.get('daily_goals', {}), indent=2)}
            - Weekly Stats: {json.dumps(user_context.get('weekly_stats', {}), indent=2)}
            - Today's Data: {json.dumps(user_context.get('today_data', {}), indent=2)}
            - Calendar Insights: {json.dumps(user_context.get('calendar_insights', {}), indent=2)}
            - Current Meal Analysis: {json.dumps(current_analysis, indent=2) if current_analysis else 'No meal being analyzed'}
            - Nutritional Insights: {', '.join(nutritional_gaps) if nutritional_gaps else 'None identified'}
            - Suggested Improvements: {json.dumps(meal_improvements, indent=2) if meal_improvements else 'None'}
            - Recent Meal History: {json.dumps(user_context.get('meal_history', [])[:3], indent=2)}
            
            Recent Chat History:
            {self.format_chat_history(chat_history[-3:])}
            
            User Message: {message}
            
            IMPORTANT: You have access to the user's complete meal history with exact dates and times. 
            If they ask about when they ate something, use the meal history data to provide specific answers.
            
            Respond in a friendly, supportive manner. If discussing the current meal, reference specific items and provide actionable advice.
            Keep response concise (2-3 sentences max) unless user asks for detailed information.
            Include emojis sparingly to keep the tone friendly.
            """
            
            # Generate response
            response = agent_model.generate_content(prompt)
            
            # Add motivational message if appropriate
            if "goal" in message.lower() or "progress" in message.lower():
                motivation = self.generate_motivational_message(user_context)
                return f"{response.text}\n\n💪 {motivation}"
            
            return response.text
            
        except Exception as e:
            print(f"Agent chat error: {e}")
            return "I'm having trouble processing that right now. Could you try rephrasing your question?"
    
    def handle_meal_memory_query(self, user_id: int, message: str) -> Optional[Dict[str, Any]]:
        """Handle meal memory queries using the MealMemoryService"""
        try:
            from app.services.meal_memory_service import MealMemoryService
            memory_service = MealMemoryService(self.db)
            
            # Check if this is a meal memory query
            query_keywords = ['when did i eat', 'what time', 'how often', 'last time', 'what did i eat with']
            
            if any(keyword in message.lower() for keyword in query_keywords):
                return memory_service.search_meals_by_natural_query(user_id, message)
            
            return None
            
        except Exception as e:
            print(f"Meal memory query error: {e}")
            return None
    
    def format_chat_history(self, history: List[Dict]) -> str:
        """Format chat history for context"""
        if not history:
            return "No previous messages"
        
        formatted = []
        for exchange in history:
            formatted.append(f"User: {exchange.get('user', '')}")
            formatted.append(f"Agent: {exchange.get('agent', '')}")
        
        return "\n".join(formatted)
    
    def generate_daily_tip(self, user_context: Dict) -> str:
        """Generate a daily health tip based on user's profile and history"""
        prompt = f"""
        Generate a personalized daily health tip for a user with this profile:
        {json.dumps(user_context, indent=2)}
        
        Make it:
        - Specific and actionable
        - Related to their goals or recent eating patterns
        - Positive and encouraging
        - One or two sentences maximum
        """
        
        try:
            response = agent_model.generate_content(prompt)
            return response.text
        except:
            indian_tips = [
                "💧 Stay hydrated with water, buttermilk, or herbal teas like tulsi chai throughout the day.",
                "🥗 Try adding one extra serving of seasonal Indian vegetables or a small bowl of dal to your meals today.",
                "🚶 A 10-minute walk after meals (especially after dinner) aids digestion - a traditional Indian practice.",
                "😴 Good sleep is crucial for metabolism - aim for 7-8 hours and avoid heavy meals 2 hours before bed.",
                "🧘 Practice mindful eating by chewing slowly and appreciating the flavors of your Indian spices.",
                "🌿 Add a pinch of turmeric to your milk or dal for its anti-inflammatory benefits.",
                "🥛 Include curd/yogurt in your meals for probiotics and better digestion.",
                "🌾 Try replacing white rice with brown rice or millets like bajra/jowar once this week.",
                "🫖 Sip on warm water with lemon and honey in the morning for better metabolism.",
                "🥜 Include a handful of nuts or seeds as a healthy snack between meals."
            ]
            import random
            return random.choice(indian_tips)
