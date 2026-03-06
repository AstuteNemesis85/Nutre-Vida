from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models.agentic_models import MealPlan, MealPlanItem, UserBehaviorPattern
from app.models.db_models import User, Meal, DailySummary
import json
import random
import google.generativeai as genai
from app.config import settings

# Configure Gemini AI
genai.configure(api_key=settings.google_api_key)
meal_planner_model = genai.GenerativeModel("models/gemini-2.0-flash")

class IntelligentMealPlanner:
    def __init__(self, db: Session):
        self.db = db
        self.indian_food_database = self._load_indian_food_database()
        self.meal_templates = self._load_meal_templates()
        
    def generate_meal_plan(
        self, 
        user_id: int, 
        plan_type: str = 'weekly',
        duration_days: int = 7,
        specific_goals: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate an intelligent meal plan for a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            # Gather user context
            user_context = self._gather_user_context(user_id)
            
            # Determine plan goals
            plan_goals = specific_goals or self._determine_plan_goals(user, user_context)
            
            # Generate meal plan structure
            meal_plan_data = self._generate_meal_plan_structure(
                user_context, 
                plan_goals, 
                duration_days
            )
            
            # Create meal plan in database
            meal_plan = self._create_meal_plan_record(
                user_id=user_id,
                plan_type=plan_type,
                duration_days=duration_days,
                goals=plan_goals,
                preferences=user_context.get('preferences', {}),
                plan_data=meal_plan_data,
                generation_context=user_context
            )
            
            if not meal_plan:
                return {'error': 'Failed to create meal plan'}
            
            # Generate detailed meal items
            meal_items = self._generate_meal_items(meal_plan.id, meal_plan_data, user_context)
            
            return {
                'meal_plan_id': meal_plan.id,
                'plan_type': plan_type,
                'duration_days': duration_days,
                'start_date': meal_plan.start_date.isoformat(),
                'end_date': meal_plan.end_date.isoformat(),
                'goals': plan_goals,
                'total_meals': len(meal_items),
                'meal_plan_data': meal_plan_data,
                'meal_items': meal_items[:10],  # Return first 10 items as preview
                'generation_summary': self._generate_plan_summary(meal_plan_data, plan_goals),
                'created_at': meal_plan.created_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error generating meal plan: {e}")
            return {'error': str(e)}
    
    def _gather_user_context(self, user_id: int) -> Dict[str, Any]:
        """Gather comprehensive user context for meal planning"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            
            # Get user patterns
            patterns = self._get_user_patterns(user_id)
            
            # Get recent meals for preference analysis
            recent_meals = self._get_recent_meals(user_id, days=30)
            
            # Get daily summaries for nutritional analysis
            daily_summaries = self._get_recent_summaries(user_id, days=14)
            
            # Analyze food preferences
            food_preferences = self._analyze_detailed_food_preferences(recent_meals)
            
            # Calculate nutritional averages
            nutritional_profile = self._calculate_nutritional_profile(daily_summaries)
            
            return {
                'user_profile': user.profile or {},
                'daily_goals': user.daily_goals or {},
                'patterns': patterns,
                'food_preferences': food_preferences,
                'nutritional_profile': nutritional_profile,
                'recent_meals_count': len(recent_meals),
                'preferences': {
                    'diet_type': user.profile.get('diet_preference', 'vegetarian'),
                    'allergies': user.profile.get('allergies', []),
                    'health_goals': user.profile.get('health_goals', []),
                    'cuisine_preference': food_preferences.get('preferred_cuisine', 'indian')
                }
            }
            
        except Exception as e:
            print(f"Error gathering user context: {e}")
            return {}
    
    def _determine_plan_goals(self, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine meal plan goals based on user profile and context"""
        goals = {
            'primary_goal': 'balanced_nutrition',
            'target_calories': context.get('daily_goals', {}).get('calories', 2000),
            'target_protein': context.get('daily_goals', {}).get('protein', 60),
            'target_carbs': 250,  # Default
            'target_fat': 65,     # Default
            'meal_frequency': 3,  # 3 main meals
            'include_snacks': True,
            'focus_areas': []
        }
        
        # Analyze nutritional profile to set focus areas
        nutritional_profile = context.get('nutritional_profile', {})
        
        if nutritional_profile.get('avg_protein', 0) < 50:
            goals['focus_areas'].append('increase_protein')
            goals['target_protein'] = max(goals['target_protein'], 70)
        
        if nutritional_profile.get('avg_calories', 0) > 2500:
            goals['focus_areas'].append('calorie_control')
            goals['target_calories'] = min(goals['target_calories'], 2200)
        
        # Set goals based on health objectives
        health_goals = context.get('preferences', {}).get('health_goals', [])
        if 'weight_loss' in health_goals:
            goals['primary_goal'] = 'weight_loss'
            goals['target_calories'] = int(goals['target_calories'] * 0.85)  # 15% reduction
            goals['focus_areas'].append('portion_control')
        elif 'weight_gain' in health_goals:
            goals['primary_goal'] = 'weight_gain'
            goals['target_calories'] = int(goals['target_calories'] * 1.15)  # 15% increase
            goals['focus_areas'].append('calorie_dense_foods')
        elif 'muscle_gain' in health_goals:
            goals['primary_goal'] = 'muscle_gain'
            goals['target_protein'] = int(goals['target_protein'] * 1.3)  # 30% increase
            goals['focus_areas'].append('high_protein')
        
        return goals
    
    def _generate_meal_plan_structure(
        self, 
        user_context: Dict[str, Any], 
        goals: Dict[str, Any], 
        duration_days: int
    ) -> Dict[str, Any]:
        """Generate the overall structure of the meal plan"""
        
        # Get eating patterns
        eating_patterns = user_context.get('patterns', {}).get('eating_time', {})
        food_preferences = user_context.get('food_preferences', {})
        
        # Create daily meal structure
        daily_structure = {
            'breakfast': {
                'target_calories': int(goals['target_calories'] * 0.25),  # 25% of daily calories
                'target_protein': int(goals['target_protein'] * 0.2),    # 20% of daily protein
                'meal_time': eating_patterns.get('avg_breakfast_time', 8.0),
                'characteristics': ['light', 'energizing', 'quick_prep']
            },
            'lunch': {
                'target_calories': int(goals['target_calories'] * 0.4),   # 40% of daily calories
                'target_protein': int(goals['target_protein'] * 0.4),     # 40% of daily protein
                'meal_time': eating_patterns.get('avg_lunch_time', 13.0),
                'characteristics': ['filling', 'balanced', 'satisfying']
            },
            'dinner': {
                'target_calories': int(goals['target_calories'] * 0.3),   # 30% of daily calories
                'target_protein': int(goals['target_protein'] * 0.3),     # 30% of daily protein
                'meal_time': eating_patterns.get('avg_dinner_time', 19.0),
                'characteristics': ['light', 'digestible', 'nutritious']
            }
        }
        
        # Add snacks if requested
        if goals.get('include_snacks', True):
            daily_structure['morning_snack'] = {
                'target_calories': int(goals['target_calories'] * 0.05),  # 5% of daily calories
                'target_protein': int(goals['target_protein'] * 0.1),     # 10% of daily protein
                'meal_time': 10.5,
                'characteristics': ['healthy', 'portable', 'energizing']
            }
        
        # Generate weekly variety plan
        weekly_themes = self._generate_weekly_themes(food_preferences, duration_days)
        
        return {
            'daily_structure': daily_structure,
            'weekly_themes': weekly_themes,
            'variety_rules': {
                'max_repeat_days': 2,  # Don't repeat same meal for more than 2 days
                'cuisine_rotation': True,
                'seasonal_focus': True
            },
            'nutritional_targets': {
                'daily_calories': goals['target_calories'],
                'daily_protein': goals['target_protein'],
                'daily_carbs': goals['target_carbs'],
                'daily_fat': goals['target_fat']
            },
            'special_considerations': goals.get('focus_areas', [])
        }
    
    def _generate_weekly_themes(self, food_preferences: Dict[str, Any], duration_days: int) -> Dict[str, str]:
        """Generate themes for each day to ensure variety"""
        themes = [
            'traditional_comfort',  # Traditional Indian comfort foods
            'protein_power',       # High protein focus
            'veggie_delight',      # Vegetable-heavy meals
            'grain_goodness',      # Focus on different grains
            'light_fresh',         # Light and fresh meals
            'regional_special',    # Regional Indian specialties
            'fusion_healthy'       # Healthy fusion options
        ]
        
        # Assign themes to days
        weekly_themes = {}
        for day in range(1, duration_days + 1):
            theme_index = (day - 1) % len(themes)
            weekly_themes[f'day_{day}'] = themes[theme_index]
        
        return weekly_themes
    
    def _generate_meal_items(
        self, 
        meal_plan_id: int, 
        plan_data: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate detailed meal items for the plan"""
        meal_items = []
        
        daily_structure = plan_data['daily_structure']
        weekly_themes = plan_data['weekly_themes']
        duration_days = len(weekly_themes)
        
        for day in range(1, duration_days + 1):
            day_theme = weekly_themes.get(f'day_{day}', 'balanced')
            
            for meal_type, meal_config in daily_structure.items():
                # Generate meal for this day and meal type
                meal_item = self._generate_single_meal(
                    meal_plan_id=meal_plan_id,
                    day_of_plan=day,
                    meal_type=meal_type,
                    meal_config=meal_config,
                    day_theme=day_theme,
                    user_context=user_context
                )
                
                if meal_item:
                    meal_items.append(meal_item)
        
        return meal_items
    
    def _generate_single_meal(
        self,
        meal_plan_id: int,
        day_of_plan: int,
        meal_type: str,
        meal_config: Dict[str, Any],
        day_theme: str,
        user_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a single meal item using AI"""
        try:
            # Create prompt for AI meal generation
            prompt = self._create_meal_generation_prompt(
                meal_type, meal_config, day_theme, user_context
            )
            
            # Generate meal using AI
            response = meal_planner_model.generate_content(prompt)
            meal_suggestion = self._parse_ai_meal_response(response.text)
            
            # Create meal plan item in database
            meal_item = MealPlanItem(
                meal_plan_id=meal_plan_id,
                day_of_plan=day_of_plan,
                meal_type=meal_type,
                food_items=meal_suggestion.get('food_items', []),
                nutritional_info=meal_suggestion.get('nutritional_info', {}),
                preparation_notes=meal_suggestion.get('preparation_notes', ''),
                alternatives=meal_suggestion.get('alternatives', [])
            )
            
            self.db.add(meal_item)
            self.db.commit()
            self.db.refresh(meal_item)
            
            return {
                'id': meal_item.id,
                'day_of_plan': day_of_plan,
                'meal_type': meal_type,
                'food_items': meal_item.food_items,
                'nutritional_info': meal_item.nutritional_info,
                'preparation_notes': meal_item.preparation_notes,
                'alternatives': meal_item.alternatives,
                'theme': day_theme
            }
            
        except Exception as e:
            print(f"Error generating single meal: {e}")
            return None
    
    def _create_meal_generation_prompt(
        self,
        meal_type: str,
        meal_config: Dict[str, Any],
        day_theme: str,
        user_context: Dict[str, Any]
    ) -> str:
        """Create AI prompt for meal generation"""
        
        preferences = user_context.get('preferences', {})
        food_preferences = user_context.get('food_preferences', {})
        
        prompt = f"""
        Generate a healthy Indian {meal_type} meal plan with the following requirements:
        
        MEAL REQUIREMENTS:
        - Target Calories: {meal_config.get('target_calories', 400)}
        - Target Protein: {meal_config.get('target_protein', 15)}g
        - Meal Type: {meal_type}
        - Theme: {day_theme}
        - Characteristics: {', '.join(meal_config.get('characteristics', []))}
        
        USER PREFERENCES:
        - Diet Type: {preferences.get('diet_type', 'vegetarian')}
        - Allergies: {', '.join(preferences.get('allergies', [])) or 'None'}
        - Health Goals: {', '.join(preferences.get('health_goals', [])) or 'General health'}
        - Preferred Cuisine: {preferences.get('cuisine_preference', 'Indian')}
        
        FOOD PREFERENCES (based on history):
        - Frequently eaten foods: {', '.join([f['food'] for f in food_preferences.get('frequent_foods', [])[:5]])}
        - Preferred cooking methods: {', '.join(food_preferences.get('cooking_methods', []))}
        
        Please provide the response in the following JSON format:
        {{
            "food_items": [
                {{
                    "name": "Food item name",
                    "quantity": "Amount (e.g., 1 cup, 2 pieces)",
                    "calories": 200,
                    "protein": 8,
                    "carbs": 30,
                    "fat": 5,
                    "fiber": 3,
                    "category": "main/side/beverage"
                }}
            ],
            "nutritional_info": {{
                "total_calories": 400,
                "total_protein": 15,
                "total_carbs": 60,
                "total_fat": 12,
                "total_fiber": 8
            }},
            "preparation_notes": "Brief cooking instructions or tips",
            "alternatives": [
                "Alternative food item 1",
                "Alternative food item 2"
            ]
        }}
        
        Focus on:
        1. Traditional Indian foods that are nutritious and balanced
        2. Seasonal and locally available ingredients
        3. Practical preparation methods
        4. Meeting the nutritional targets
        5. Variety and taste appeal
        """
        
        return prompt
    
    def _parse_ai_meal_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response into structured meal data"""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback: create a basic structure
                return self._create_fallback_meal()
                
        except json.JSONDecodeError:
            print("Failed to parse AI response, using fallback")
            return self._create_fallback_meal()
    
    def _create_fallback_meal(self) -> Dict[str, Any]:
        """Create a fallback meal when AI parsing fails"""
        return {
            "food_items": [
                {
                    "name": "Dal Rice",
                    "quantity": "1 cup each",
                    "calories": 350,
                    "protein": 12,
                    "carbs": 65,
                    "fat": 4,
                    "fiber": 6,
                    "category": "main"
                }
            ],
            "nutritional_info": {
                "total_calories": 350,
                "total_protein": 12,
                "total_carbs": 65,
                "total_fat": 4,
                "total_fiber": 6
            },
            "preparation_notes": "Cook dal and rice separately, serve together with ghee",
            "alternatives": ["Khichdi", "Sambar Rice"]
        }
    
    def get_user_meal_plans(self, user_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all meal plans for a user"""
        try:
            query = self.db.query(MealPlan).filter(MealPlan.user_id == user_id)
            
            if active_only:
                query = query.filter(MealPlan.is_active == True)
            
            meal_plans = query.order_by(desc(MealPlan.created_at)).all()
            
            return [
                {
                    'id': plan.id,
                    'plan_name': plan.plan_name,
                    'plan_type': plan.plan_type,
                    'start_date': plan.start_date.isoformat(),
                    'end_date': plan.end_date.isoformat(),
                    'goals': plan.goals,
                    'is_active': plan.is_active,
                    'adherence_score': plan.adherence_score,
                    'created_at': plan.created_at.isoformat()
                }
                for plan in meal_plans
            ]
            
        except Exception as e:
            print(f"Error getting user meal plans: {e}")
            return []
    
    def get_meal_plan_details(self, meal_plan_id: int, user_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific meal plan"""
        try:
            meal_plan = self.db.query(MealPlan).filter(
                and_(
                    MealPlan.id == meal_plan_id,
                    MealPlan.user_id == user_id
                )
            ).first()
            
            if not meal_plan:
                return {'error': 'Meal plan not found'}
            
            # Get meal items
            meal_items = self.db.query(MealPlanItem).filter(
                MealPlanItem.meal_plan_id == meal_plan_id
            ).order_by(MealPlanItem.day_of_plan, MealPlanItem.meal_type).all()
            
            # Group items by day
            items_by_day = {}
            for item in meal_items:
                day_key = f'day_{item.day_of_plan}'
                if day_key not in items_by_day:
                    items_by_day[day_key] = {}
                
                items_by_day[day_key][item.meal_type] = {
                    'id': item.id,
                    'food_items': item.food_items,
                    'nutritional_info': item.nutritional_info,
                    'preparation_notes': item.preparation_notes,
                    'alternatives': item.alternatives,
                    'is_completed': item.is_completed,
                    'completion_date': item.completion_date.isoformat() if item.completion_date else None
                }
            
            return {
                'id': meal_plan.id,
                'plan_name': meal_plan.plan_name,
                'plan_type': meal_plan.plan_type,
                'start_date': meal_plan.start_date.isoformat(),
                'end_date': meal_plan.end_date.isoformat(),
                'goals': meal_plan.goals,
                'preferences': meal_plan.preferences,
                'plan_data': meal_plan.plan_data,
                'is_active': meal_plan.is_active,
                'adherence_score': meal_plan.adherence_score,
                'items_by_day': items_by_day,
                'total_items': len(meal_items),
                'completed_items': len([item for item in meal_items if item.is_completed]),
                'created_at': meal_plan.created_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error getting meal plan details: {e}")
            return {'error': str(e)}
    
    def mark_meal_completed(self, meal_item_id: int, user_id: int) -> bool:
        """Mark a meal plan item as completed"""
        try:
            # Verify the meal item belongs to the user
            meal_item = self.db.query(MealPlanItem).join(MealPlan).filter(
                and_(
                    MealPlanItem.id == meal_item_id,
                    MealPlan.user_id == user_id
                )
            ).first()
            
            if not meal_item:
                return False
            
            meal_item.is_completed = True
            meal_item.completion_date = datetime.now()
            
            # Update adherence score for the meal plan
            self._update_adherence_score(meal_item.meal_plan_id)
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error marking meal completed: {e}")
            self.db.rollback()
            return False
    
    def _update_adherence_score(self, meal_plan_id: int):
        """Update the adherence score for a meal plan"""
        try:
            meal_plan = self.db.query(MealPlan).filter(MealPlan.id == meal_plan_id).first()
            if not meal_plan:
                return
            
            # Get all meal items for this plan
            meal_items = self.db.query(MealPlanItem).filter(
                MealPlanItem.meal_plan_id == meal_plan_id
            ).all()
            
            if not meal_items:
                return
            
            # Calculate adherence score
            completed_items = len([item for item in meal_items if item.is_completed])
            total_items = len(meal_items)
            adherence_score = (completed_items / total_items) * 100
            
            meal_plan.adherence_score = round(adherence_score, 1)
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating adherence score: {e}")
            self.db.rollback()
    
    # Helper methods
    def _get_user_patterns(self, user_id: int) -> Dict[str, Any]:
        """Get user behavior patterns"""
        try:
            patterns = self.db.query(UserBehaviorPattern).filter(
                UserBehaviorPattern.user_id == user_id
            ).all()
            
            pattern_dict = {}
            for pattern in patterns:
                pattern_dict[pattern.pattern_type] = pattern.pattern_data
            
            return pattern_dict
            
        except Exception as e:
            print(f"Error getting user patterns: {e}")
            return {}
    
    def _get_recent_meals(self, user_id: int, days: int = 30) -> List[Meal]:
        """Get recent meals for analysis"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            return self.db.query(Meal).filter(
                and_(
                    Meal.user_id == user_id,
                    Meal.upload_time >= cutoff_date
                )
            ).order_by(desc(Meal.upload_time)).all()
            
        except Exception as e:
            print(f"Error getting recent meals: {e}")
            return []
    
    def _get_recent_summaries(self, user_id: int, days: int = 14) -> List[DailySummary]:
        """Get recent daily summaries"""
        try:
            cutoff_date = date.today() - timedelta(days=days)
            return self.db.query(DailySummary).filter(
                and_(
                    DailySummary.user_id == user_id,
                    DailySummary.date >= cutoff_date
                )
            ).order_by(desc(DailySummary.date)).all()
            
        except Exception as e:
            print(f"Error getting recent summaries: {e}")
            return []
    
    def _analyze_detailed_food_preferences(self, meals: List[Meal]) -> Dict[str, Any]:
        """Analyze detailed food preferences from meal history"""
        food_counts = {}
        cooking_methods = {}
        cuisine_types = {}
        
        for meal in meals:
            if meal.analysis_data and meal.analysis_data.get('items'):
                for item in meal.analysis_data['items']:
                    food_name = item.get('name', '').lower()
                    if food_name:
                        food_counts[food_name] = food_counts.get(food_name, 0) + 1
                    
                    # Analyze cooking methods and cuisine
                    if 'fried' in food_name:
                        cooking_methods['fried'] = cooking_methods.get('fried', 0) + 1
                    elif any(word in food_name for word in ['steamed', 'boiled']):
                        cooking_methods['steamed'] = cooking_methods.get('steamed', 0) + 1
                    elif any(word in food_name for word in ['grilled', 'roasted']):
                        cooking_methods['grilled'] = cooking_methods.get('grilled', 0) + 1
                    
                    # Cuisine classification
                    if any(word in food_name for word in ['dal', 'curry', 'rice', 'roti', 'sabzi']):
                        cuisine_types['indian'] = cuisine_types.get('indian', 0) + 1
                    elif any(word in food_name for word in ['pasta', 'pizza', 'bread']):
                        cuisine_types['western'] = cuisine_types.get('western', 0) + 1
        
        # Get top preferences
        frequent_foods = [
            {'food': food, 'count': count} 
            for food, count in sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        preferred_cuisine = max(cuisine_types.items(), key=lambda x: x[1])[0] if cuisine_types else 'indian'
        
        return {
            'frequent_foods': frequent_foods,
            'cooking_methods': list(cooking_methods.keys()),
            'preferred_cuisine': preferred_cuisine,
            'cuisine_distribution': cuisine_types,
            'total_meals_analyzed': len(meals)
        }
    
    def _calculate_nutritional_profile(self, daily_summaries: List[DailySummary]) -> Dict[str, Any]:
        """Calculate user's nutritional profile from daily summaries"""
        if not daily_summaries:
            return {}
        
        import statistics
        
        calories = [s.total_calories for s in daily_summaries if s.total_calories > 0]
        proteins = [s.total_protein for s in daily_summaries if s.total_protein > 0]
        carbs = [s.total_carbs for s in daily_summaries if s.total_carbs > 0]
        fats = [s.total_fat for s in daily_summaries if s.total_fat > 0]
        
        return {
            'avg_calories': round(statistics.mean(calories), 1) if calories else 0,
            'avg_protein': round(statistics.mean(proteins), 1) if proteins else 0,
            'avg_carbs': round(statistics.mean(carbs), 1) if carbs else 0,
            'avg_fat': round(statistics.mean(fats), 1) if fats else 0,
            'calorie_consistency': round(statistics.stdev(calories), 1) if len(calories) > 1 else 0,
            'days_analyzed': len(daily_summaries)
        }
    
    def _create_meal_plan_record(self, **kwargs) -> Optional[MealPlan]:
        """Create a meal plan record in the database"""
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=kwargs['duration_days'] - 1)
            
            meal_plan = MealPlan(
                user_id=kwargs['user_id'],
                plan_name=f"{kwargs['plan_type'].title()} Plan - {start_date.strftime('%B %d')}",
                plan_type=kwargs['plan_type'],
                start_date=start_date,
                end_date=end_date,
                goals=kwargs['goals'],
                preferences=kwargs['preferences'],
                plan_data=kwargs['plan_data'],
                generation_context=kwargs['generation_context']
            )
            
            self.db.add(meal_plan)
            self.db.commit()
            self.db.refresh(meal_plan)
            
            return meal_plan
            
        except Exception as e:
            print(f"Error creating meal plan record: {e}")
            self.db.rollback()
            return None
    
    def _generate_plan_summary(self, plan_data: Dict[str, Any], goals: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the meal plan"""
        daily_structure = plan_data.get('daily_structure', {})
        
        total_daily_calories = sum(meal.get('target_calories', 0) for meal in daily_structure.values())
        total_daily_protein = sum(meal.get('target_protein', 0) for meal in daily_structure.values())
        
        return {
            'primary_goal': goals.get('primary_goal', 'balanced_nutrition'),
            'daily_targets': {
                'calories': total_daily_calories,
                'protein': total_daily_protein,
                'meals_per_day': len(daily_structure)
            },
            'focus_areas': goals.get('focus_areas', []),
            'variety_themes': len(plan_data.get('weekly_themes', {})),
            'special_considerations': plan_data.get('special_considerations', [])
        }
    
    def _load_indian_food_database(self) -> Dict[str, Any]:
        """Load Indian food database for meal planning"""
        return {
            'breakfast': {
                'traditional': ['idli', 'dosa', 'upma', 'poha', 'paratha', 'uttapam'],
                'healthy': ['oats', 'daliya', 'quinoa porridge', 'millet porridge'],
                'quick': ['bread toast', 'cornflakes', 'fruits', 'smoothie']
            },
            'lunch': {
                'traditional': ['dal rice', 'rajma rice', 'chole bhature', 'biryani'],
                'healthy': ['quinoa salad', 'brown rice', 'millet meals', 'vegetable curry'],
                'regional': ['sambar rice', 'rasam rice', 'kadhi chawal', 'pav bhaji']
            },
            'dinner': {
                'light': ['khichdi', 'soup', 'salad', 'dal roti'],
                'traditional': ['sabzi roti', 'dal chawal', 'curry rice'],
                'healthy': ['grilled vegetables', 'steamed food', 'light curry']
            },
            'snacks': {
                'healthy': ['fruits', 'nuts', 'yogurt', 'sprouts'],
                'traditional': ['samosa', 'pakora', 'chaat', 'namkeen'],
                'protein': ['paneer', 'boiled eggs', 'protein bars', 'dal dhokla']
            }
        }
    
    def _load_meal_templates(self) -> Dict[str, Any]:
        """Load meal templates for different goals"""
        return {
            'weight_loss': {
                'breakfast': {'calories': 300, 'protein': 15, 'carbs': 40, 'fat': 10},
                'lunch': {'calories': 400, 'protein': 20, 'carbs': 50, 'fat': 15},
                'dinner': {'calories': 350, 'protein': 18, 'carbs': 35, 'fat': 12},
                'snack': {'calories': 150, 'protein': 8, 'carbs': 15, 'fat': 6}
            },
            'weight_gain': {
                'breakfast': {'calories': 500, 'protein': 20, 'carbs': 65, 'fat': 18},
                'lunch': {'calories': 700, 'protein': 30, 'carbs': 85, 'fat': 25},
                'dinner': {'calories': 600, 'protein': 25, 'carbs': 70, 'fat': 22},
                'snack': {'calories': 300, 'protein': 12, 'carbs': 35, 'fat': 12}
            },
            'balanced_nutrition': {
                'breakfast': {'calories': 400, 'protein': 15, 'carbs': 55, 'fat': 15},
                'lunch': {'calories': 550, 'protein': 25, 'carbs': 70, 'fat': 20},
                'dinner': {'calories': 450, 'protein': 20, 'carbs': 55, 'fat': 18},
                'snack': {'calories': 200, 'protein': 8, 'carbs': 25, 'fat': 8}
            }
        }
