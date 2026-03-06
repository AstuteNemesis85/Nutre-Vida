from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from app.models.db_models import User, Meal, DailySummary
import re
from difflib import SequenceMatcher

class MealMemoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_meals_by_food_name(self, user_id: int, food_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for meals containing specific food items using semantic matching"""
        try:
            # Get all meals for the user
            meals = self.db.query(Meal).filter(
                Meal.user_id == user_id
            ).order_by(Meal.upload_time.desc()).limit(100).all()  # Search in recent 100 meals
            
            matching_meals = []
            food_name_lower = food_name.lower()
            
            for meal in meals:
                if not meal.analysis_data or not meal.analysis_data.get('items'):
                    continue
                
                # Check each food item in the meal
                for item in meal.analysis_data.get('items', []):
                    item_name = item.get('name', '').lower()
                    
                    # Multiple matching strategies
                    similarity_score = self._calculate_food_similarity(food_name_lower, item_name)
                    
                    if similarity_score > 0.6:  # 60% similarity threshold
                        meal_data = {
                            'meal_id': meal.id,
                            'upload_date': meal.upload_date.isoformat() if meal.upload_date else None,
                            'upload_time': meal.upload_time.isoformat() if meal.upload_time else None,
                            'day_of_week': meal.day_of_week,
                            'matched_item': item,
                            'similarity_score': similarity_score,
                            'all_items': meal.analysis_data.get('items', []),
                            'total_calories': meal.analysis_data.get('total_calories', 0),
                            'meal_type': self._determine_meal_type(meal.upload_time) if meal.upload_time else 'unknown'
                        }
                        matching_meals.append(meal_data)
                        break  # Found a match in this meal, move to next meal
            
            # Sort by similarity score and upload time
            matching_meals.sort(key=lambda x: (x['similarity_score'], x['upload_time']), reverse=True)
            
            return matching_meals[:limit]
            
        except Exception as e:
            print(f"Error searching meals by food name: {e}")
            return []
    
    def _calculate_food_similarity(self, search_term: str, food_name: str) -> float:
        """Calculate similarity between search term and food name using multiple strategies"""
        
        # Strategy 1: Exact substring match
        if search_term in food_name or food_name in search_term:
            return 1.0
        
        # Strategy 2: Word-based matching
        search_words = set(search_term.split())
        food_words = set(food_name.split())
        
        if search_words.intersection(food_words):
            word_overlap = len(search_words.intersection(food_words))
            total_words = len(search_words.union(food_words))
            word_similarity = word_overlap / total_words
            if word_similarity > 0.5:
                return word_similarity
        
        # Strategy 3: Sequence matching
        sequence_similarity = SequenceMatcher(None, search_term, food_name).ratio()
        
        # Strategy 4: Common Indian food variations
        variations = self._get_food_variations(search_term)
        for variation in variations:
            if variation in food_name:
                return 0.9
        
        return max(sequence_similarity, 0.0)
    
    def _get_food_variations(self, food_name: str) -> List[str]:
        """Get common variations of Indian food names"""
        variations = []
        
        # Common Indian food variations
        food_mappings = {
            'dosa': ['dosai', 'dose', 'dosa', 'masala dosa', 'plain dosa'],
            'masala dosa': ['masala dosai', 'masala dose', 'dosa masala'],
            'idli': ['idly', 'idli', 'steamed rice cake'],
            'biryani': ['biriyani', 'biryani', 'dum biryani', 'chicken biryani'],
            'roti': ['chapati', 'roti', 'indian bread', 'wheat bread'],
            'dal': ['daal', 'lentil', 'dal curry', 'lentil curry'],
            'rice': ['steamed rice', 'white rice', 'basmati rice'],
            'curry': ['sabzi', 'vegetable curry', 'gravy'],
            'samosa': ['samosa', 'punjabi samosa', 'fried samosa'],
            'paratha': ['parantha', 'stuffed paratha', 'aloo paratha']
        }
        
        food_lower = food_name.lower()
        for key, values in food_mappings.items():
            if key in food_lower or food_lower in key:
                variations.extend(values)
        
        return variations
    
    def get_food_frequency_analysis(self, user_id: int, food_name: str, days: int = 30) -> Dict[str, Any]:
        """Analyze how frequently a user eats a specific food"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            matching_meals = self.search_meals_by_food_name(user_id, food_name, limit=50)
            
            # Filter by date range
            recent_meals = [
                meal for meal in matching_meals 
                if meal['upload_date'] and date.fromisoformat(meal['upload_date']) >= start_date
            ]
            
            if not recent_meals:
                return {
                    'food_name': food_name,
                    'frequency': 0,
                    'total_occurrences': 0,
                    'days_analyzed': days,
                    'average_days_between': 0,
                    'last_eaten': None,
                    'most_common_meal_type': None,
                    'total_calories_consumed': 0
                }
            
            # Calculate statistics
            total_occurrences = len(recent_meals)
            frequency_per_week = (total_occurrences / days) * 7
            
            # Calculate days between meals
            dates = [date.fromisoformat(meal['upload_date']) for meal in recent_meals]
            dates.sort()
            
            days_between = []
            for i in range(1, len(dates)):
                days_between.append((dates[i] - dates[i-1]).days)
            
            avg_days_between = sum(days_between) / len(days_between) if days_between else 0
            
            # Most common meal type
            meal_types = [meal['meal_type'] for meal in recent_meals]
            most_common_meal_type = max(set(meal_types), key=meal_types.count) if meal_types else None
            
            # Total calories from this food
            total_calories = sum(meal['matched_item'].get('calories', 0) for meal in recent_meals)
            
            return {
                'food_name': food_name,
                'frequency_per_week': round(frequency_per_week, 2),
                'total_occurrences': total_occurrences,
                'days_analyzed': days,
                'average_days_between': round(avg_days_between, 1),
                'last_eaten': recent_meals[0]['upload_date'] if recent_meals else None,
                'last_eaten_time': recent_meals[0]['upload_time'] if recent_meals else None,
                'most_common_meal_type': most_common_meal_type,
                'total_calories_consumed': total_calories,
                'recent_meals': recent_meals[:5]  # Last 5 occurrences
            }
            
        except Exception as e:
            print(f"Error in frequency analysis: {e}")
            return {'error': str(e)}
    
    def get_meal_context(self, user_id: int, meal_id: int) -> Dict[str, Any]:
        """Get complete context of a specific meal including what was eaten together"""
        try:
            meal = self.db.query(Meal).filter(
                and_(Meal.id == meal_id, Meal.user_id == user_id)
            ).first()
            
            if not meal:
                return {'error': 'Meal not found'}
            
            # Get meals from the same day
            same_day_meals = self.db.query(Meal).filter(
                and_(
                    Meal.user_id == user_id,
                    Meal.upload_date == meal.upload_date,
                    Meal.id != meal_id
                )
            ).order_by(Meal.upload_time).all()
            
            return {
                'target_meal': {
                    'id': meal.id,
                    'upload_date': meal.upload_date.isoformat() if meal.upload_date else None,
                    'upload_time': meal.upload_time.isoformat() if meal.upload_time else None,
                    'day_of_week': meal.day_of_week,
                    'meal_type': self._determine_meal_type(meal.upload_time) if meal.upload_time else 'unknown',
                    'items': meal.analysis_data.get('items', []) if meal.analysis_data else [],
                    'total_calories': meal.analysis_data.get('total_calories', 0) if meal.analysis_data else 0,
                    'nutrition': {
                        'protein': meal.analysis_data.get('total_protein', 0) if meal.analysis_data else 0,
                        'carbs': meal.analysis_data.get('total_carbs', 0) if meal.analysis_data else 0,
                        'fat': meal.analysis_data.get('total_fat', 0) if meal.analysis_data else 0
                    }
                },
                'same_day_meals': [
                    {
                        'id': m.id,
                        'upload_time': m.upload_time.isoformat() if m.upload_time else None,
                        'meal_type': self._determine_meal_type(m.upload_time) if m.upload_time else 'unknown',
                        'items': [item.get('name', 'Unknown') for item in m.analysis_data.get('items', [])] if m.analysis_data else [],
                        'calories': m.analysis_data.get('total_calories', 0) if m.analysis_data else 0
                    }
                    for m in same_day_meals
                ]
            }
            
        except Exception as e:
            print(f"Error getting meal context: {e}")
            return {'error': str(e)}
    
    def _determine_meal_type(self, meal_time: datetime) -> str:
        """Determine meal type based on time of day"""
        if not meal_time:
            return 'unknown'
        
        hour = meal_time.hour
        
        if 5 <= hour < 11:
            return "breakfast"
        elif 11 <= hour < 16:
            return "lunch"
        elif 16 <= hour < 21:
            return "dinner"
        else:
            return "snack"
    
    def search_meals_by_natural_query(self, user_id: int, query: str) -> Dict[str, Any]:
        """Process natural language queries about meals"""
        query_lower = query.lower()
        
        # Query type detection
        if any(word in query_lower for word in ['when', 'what time', 'date']):
            return self._handle_when_query(user_id, query_lower)
        elif any(word in query_lower for word in ['how often', 'frequency', 'how many times']):
            return self._handle_frequency_query(user_id, query_lower)
        elif any(word in query_lower for word in ['what did i eat with', 'what else', 'together']):
            return self._handle_context_query(user_id, query_lower)
        elif any(word in query_lower for word in ['last time', 'recent', 'latest']):
            return self._handle_last_time_query(user_id, query_lower)
        else:
            # Default to food search
            return self._handle_general_food_search(user_id, query_lower)
    
    def _handle_when_query(self, user_id: int, query: str) -> Dict[str, Any]:
        """Handle 'when did I eat...' queries"""
        # Extract food name from query
        food_name = self._extract_food_name_from_query(query)
        
        if not food_name:
            return {'error': 'Could not identify food item in query'}
        
        matching_meals = self.search_meals_by_food_name(user_id, food_name, limit=5)
        
        if not matching_meals:
            return {
                'query_type': 'when',
                'food_name': food_name,
                'result': f"I couldn't find any record of you eating {food_name}. Maybe try a different name or check if it was part of a larger meal?"
            }
        
        latest_meal = matching_meals[0]
        
        # Format the response
        upload_time = datetime.fromisoformat(latest_meal['upload_time'])
        formatted_date = upload_time.strftime("%B %d, %Y")
        formatted_time = upload_time.strftime("%I:%M %p")
        day_of_week = latest_meal['day_of_week']
        
        response = f"You last ate {food_name} on {day_of_week}, {formatted_date} at {formatted_time}."
        
        if len(matching_meals) > 1:
            response += f" You've had it {len(matching_meals)} times in your recent meals."
        
        return {
            'query_type': 'when',
            'food_name': food_name,
            'result': response,
            'exact_datetime': latest_meal['upload_time'],
            'meal_details': latest_meal,
            'total_occurrences': len(matching_meals)
        }
    
    def _handle_frequency_query(self, user_id: int, query: str) -> Dict[str, Any]:
        """Handle 'how often do I eat...' queries"""
        food_name = self._extract_food_name_from_query(query)
        
        if not food_name:
            return {'error': 'Could not identify food item in query'}
        
        frequency_data = self.get_food_frequency_analysis(user_id, food_name, days=30)
        
        if frequency_data.get('total_occurrences', 0) == 0:
            return {
                'query_type': 'frequency',
                'food_name': food_name,
                'result': f"You haven't eaten {food_name} in the last 30 days, or it might be recorded under a different name."
            }
        
        freq_per_week = frequency_data['frequency_per_week']
        total_times = frequency_data['total_occurrences']
        
        if freq_per_week >= 3:
            frequency_desc = "quite often"
        elif freq_per_week >= 1:
            frequency_desc = "regularly"
        else:
            frequency_desc = "occasionally"
        
        response = f"You eat {food_name} {frequency_desc} - about {freq_per_week} times per week. "
        response += f"In the last 30 days, you've had it {total_times} times."
        
        if frequency_data['most_common_meal_type']:
            response += f" You usually have it for {frequency_data['most_common_meal_type']}."
        
        return {
            'query_type': 'frequency',
            'food_name': food_name,
            'result': response,
            'frequency_data': frequency_data
        }
    
    def _handle_context_query(self, user_id: int, query: str) -> Dict[str, Any]:
        """Handle 'what did I eat with...' queries"""
        food_name = self._extract_food_name_from_query(query)
        
        if not food_name:
            return {'error': 'Could not identify food item in query'}
        
        matching_meals = self.search_meals_by_food_name(user_id, food_name, limit=3)
        
        if not matching_meals:
            return {
                'query_type': 'context',
                'food_name': food_name,
                'result': f"I couldn't find any record of you eating {food_name}."
            }
        
        # Get context for the most recent meal
        latest_meal = matching_meals[0]
        context = self.get_meal_context(user_id, latest_meal['meal_id'])
        
        if context.get('error'):
            return {'error': context['error']}
        
        target_meal = context['target_meal']
        other_items = [item['name'] for item in target_meal['items'] if food_name.lower() not in item['name'].lower()]
        
        response = f"The last time you had {food_name}, you also ate: {', '.join(other_items)}." if other_items else f"You had {food_name} by itself."
        
        # Add same-day context
        same_day_items = []
        for meal in context['same_day_meals']:
            same_day_items.extend(meal['items'])
        
        if same_day_items:
            response += f" That day you also had: {', '.join(same_day_items)}."
        
        return {
            'query_type': 'context',
            'food_name': food_name,
            'result': response,
            'meal_context': context
        }
    
    def _handle_last_time_query(self, user_id: int, query: str) -> Dict[str, Any]:
        """Handle 'last time I ate...' queries"""
        return self._handle_when_query(user_id, query)  # Same logic as when query
    
    def _handle_general_food_search(self, user_id: int, query: str) -> Dict[str, Any]:
        """Handle general food search queries"""
        matching_meals = self.search_meals_by_food_name(user_id, query, limit=5)
        
        if not matching_meals:
            return {
                'query_type': 'search',
                'search_term': query,
                'result': f"I couldn't find any meals matching '{query}'. Try using different keywords or check your meal history."
            }
        
        response = f"I found {len(matching_meals)} meals matching '{query}':\n"
        
        for i, meal in enumerate(matching_meals[:3], 1):
            upload_time = datetime.fromisoformat(meal['upload_time'])
            formatted_date = upload_time.strftime("%B %d")
            response += f"{i}. {formatted_date} - {meal['matched_item']['name']} ({meal['matched_item'].get('calories', 'N/A')} cal)\n"
        
        return {
            'query_type': 'search',
            'search_term': query,
            'result': response.strip(),
            'matching_meals': matching_meals
        }
    
    def _extract_food_name_from_query(self, query: str) -> str:
        """Extract food name from natural language query"""
        # Remove common query words
        stop_words = ['when', 'did', 'i', 'eat', 'have', 'what', 'time', 'how', 'often', 'do', 'last', 'with', 'together']
        
        words = query.split()
        food_words = [word for word in words if word.lower() not in stop_words and len(word) > 2]
        
        # Join remaining words as potential food name
        return ' '.join(food_words)
