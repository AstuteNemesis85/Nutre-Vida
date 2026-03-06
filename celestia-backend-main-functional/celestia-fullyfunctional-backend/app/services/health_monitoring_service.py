from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from app.models.agentic_models import HealthAlert, UserBehaviorPattern, PredictiveInsight
from app.models.db_models import User, Meal, DailySummary
import json
import statistics

class HealthMonitoringService:
    def __init__(self, db: Session):
        self.db = db
        self.alert_thresholds = {
            'calorie_excess': 500,  # Calories above goal
            'calorie_deficit': 300,  # Calories below goal
            'protein_deficit': 20,   # Grams below recommended
            'consecutive_days_concern': 3,  # Days of concerning pattern
            'weight_change_concern': 2.0,  # Kg change threshold
        }
    
    def run_health_monitoring(self, user_id: int) -> Dict[str, Any]:
        """Run comprehensive health monitoring for a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            # Get recent data for analysis
            recent_meals = self._get_recent_meals(user_id, days=14)
            daily_summaries = self._get_recent_summaries(user_id, days=14)
            
            # Run various monitoring checks
            alerts_generated = []
            patterns_updated = []
            insights_generated = []
            
            # 1. Nutritional monitoring
            nutrition_alerts = self._monitor_nutrition_patterns(user_id, recent_meals, daily_summaries)
            alerts_generated.extend(nutrition_alerts)
            
            # 2. Eating pattern monitoring
            pattern_alerts = self._monitor_eating_patterns(user_id, recent_meals)
            alerts_generated.extend(pattern_alerts)
            
            # 3. Goal adherence monitoring
            goal_alerts = self._monitor_goal_adherence(user_id, daily_summaries, user.daily_goals)
            alerts_generated.extend(goal_alerts)
            
            # 4. Update behavior patterns
            updated_patterns = self._update_behavior_patterns(user_id, recent_meals, daily_summaries)
            patterns_updated.extend(updated_patterns)
            
            # 5. Generate predictive insights
            predictions = self._generate_predictive_insights(user_id, recent_meals, daily_summaries)
            insights_generated.extend(predictions)
            
            # 6. Health risk assessment
            risk_alerts = self._assess_health_risks(user_id, recent_meals, daily_summaries)
            alerts_generated.extend(risk_alerts)
            
            return {
                'monitoring_completed': True,
                'alerts_generated': len(alerts_generated),
                'patterns_updated': len(patterns_updated),
                'insights_generated': len(insights_generated),
                'alerts': alerts_generated,
                'patterns': patterns_updated,
                'insights': insights_generated,
                'monitoring_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in health monitoring: {e}")
            return {'error': str(e)}
    
    def _monitor_nutrition_patterns(
        self, 
        user_id: int, 
        recent_meals: List[Meal], 
        daily_summaries: List[DailySummary]
    ) -> List[Dict[str, Any]]:
        """Monitor nutritional patterns and generate alerts"""
        alerts = []
        
        if not daily_summaries:
            return alerts
        
        # Calculate average daily nutrition
        avg_calories = statistics.mean([s.total_calories for s in daily_summaries if s.total_calories > 0])
        avg_protein = statistics.mean([s.total_protein for s in daily_summaries if s.total_protein > 0])
        avg_carbs = statistics.mean([s.total_carbs for s in daily_summaries if s.total_carbs > 0])
        avg_fat = statistics.mean([s.total_fat for s in daily_summaries if s.total_fat > 0])
        
        # Check for concerning patterns
        
        # 1. Consistently low protein intake
        low_protein_days = len([s for s in daily_summaries if s.total_protein < 50])
        if low_protein_days >= 3:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='nutrition_gap',
                severity='medium',
                title='Low Protein Intake Detected',
                message=f'You\'ve had low protein intake for {low_protein_days} days. Consider adding dal, paneer, eggs, or nuts to your meals.',
                data_context={
                    'avg_protein': round(avg_protein, 1),
                    'low_protein_days': low_protein_days,
                    'recommended_protein': 60,
                    'suggestions': ['Add dal to lunch and dinner', 'Include paneer or curd', 'Snack on nuts or seeds']
                }
            )
            alerts.append(alert)
        
        # 2. Excessive calorie intake pattern
        high_calorie_days = len([s for s in daily_summaries if s.total_calories > 2500])
        if high_calorie_days >= 3:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='calorie_excess',
                severity='medium',
                title='High Calorie Intake Pattern',
                message=f'You\'ve exceeded 2500 calories for {high_calorie_days} days. Consider portion control and lighter evening meals.',
                data_context={
                    'avg_calories': round(avg_calories, 1),
                    'high_calorie_days': high_calorie_days,
                    'suggestions': ['Reduce rice/roti portions', 'Use less oil in cooking', 'Add more vegetables']
                }
            )
            alerts.append(alert)
        
        # 3. Imbalanced macronutrient ratios
        if avg_calories > 0:
            protein_percent = (avg_protein * 4 / avg_calories) * 100
            carbs_percent = (avg_carbs * 4 / avg_calories) * 100
            fat_percent = (avg_fat * 9 / avg_calories) * 100
            
            if carbs_percent > 70:
                alert = self._create_alert(
                    user_id=user_id,
                    alert_type='nutrition_gap',
                    severity='low',
                    title='High Carbohydrate Intake',
                    message=f'Your diet is {carbs_percent:.1f}% carbohydrates. Consider balancing with more protein and healthy fats.',
                    data_context={
                        'carbs_percent': round(carbs_percent, 1),
                        'protein_percent': round(protein_percent, 1),
                        'fat_percent': round(fat_percent, 1),
                        'suggestions': ['Replace some rice with dal', 'Add nuts to meals', 'Include more protein sources']
                    }
                )
                alerts.append(alert)
        
        # 4. Micronutrient concerns (based on food variety)
        food_variety = self._analyze_food_variety(recent_meals)
        if food_variety['unique_foods'] < 15:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='nutrition_gap',
                severity='low',
                title='Limited Food Variety',
                message=f'You\'ve eaten only {food_variety["unique_foods"]} different foods recently. Try adding more variety for better nutrition.',
                data_context={
                    'unique_foods': food_variety['unique_foods'],
                    'common_foods': food_variety['most_common'],
                    'suggestions': ['Try seasonal vegetables', 'Experiment with different dals', 'Add fruits as snacks']
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _monitor_eating_patterns(self, user_id: int, recent_meals: List[Meal]) -> List[Dict[str, Any]]:
        """Monitor eating patterns and timing"""
        alerts = []
        
        if len(recent_meals) < 5:
            return alerts
        
        # Analyze meal timing patterns
        meal_times = []
        late_dinners = 0
        skipped_breakfasts = 0
        
        # Group meals by date
        meals_by_date = {}
        for meal in recent_meals:
            meal_date = meal.upload_date
            if meal_date not in meals_by_date:
                meals_by_date[meal_date] = []
            meals_by_date[meal_date].append(meal)
        
        for date_meals in meals_by_date.values():
            # Check for late dinners (after 9 PM)
            dinner_meals = [m for m in date_meals if m.upload_time and m.upload_time.hour >= 19]
            if any(m.upload_time.hour >= 21 for m in dinner_meals):
                late_dinners += 1
            
            # Check for skipped breakfasts (no meal before 11 AM)
            breakfast_meals = [m for m in date_meals if m.upload_time and m.upload_time.hour <= 11]
            if not breakfast_meals:
                skipped_breakfasts += 1
        
        # Generate alerts for concerning patterns
        total_days = len(meals_by_date)
        
        if late_dinners >= 3:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='pattern_concern',
                severity='medium',
                title='Late Dinner Pattern Detected',
                message=f'You\'ve had late dinners (after 9 PM) for {late_dinners} days. This can affect sleep and digestion.',
                data_context={
                    'late_dinners': late_dinners,
                    'total_days': total_days,
                    'suggestions': ['Try to eat dinner by 8 PM', 'Have lighter evening meals', 'Avoid heavy foods before bed']
                }
            )
            alerts.append(alert)
        
        if skipped_breakfasts >= 3:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='pattern_concern',
                severity='medium',
                title='Breakfast Skipping Pattern',
                message=f'You\'ve skipped breakfast for {skipped_breakfasts} days. Breakfast helps kickstart your metabolism.',
                data_context={
                    'skipped_breakfasts': skipped_breakfasts,
                    'total_days': total_days,
                    'suggestions': ['Start with simple options like banana and milk', 'Prepare overnight oats', 'Keep fruits handy']
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _monitor_goal_adherence(
        self, 
        user_id: int, 
        daily_summaries: List[DailySummary], 
        daily_goals: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Monitor adherence to daily goals"""
        alerts = []
        
        if not daily_goals or not daily_summaries:
            return alerts
        
        goal_calories = daily_goals.get('calories', 2000)
        goal_protein = daily_goals.get('protein', 60)
        
        # Calculate goal adherence
        calorie_misses = 0
        protein_misses = 0
        
        for summary in daily_summaries:
            if abs(summary.total_calories - goal_calories) > self.alert_thresholds['calorie_excess']:
                calorie_misses += 1
            if summary.total_protein < (goal_protein - self.alert_thresholds['protein_deficit']):
                protein_misses += 1
        
        # Generate alerts for poor adherence
        if calorie_misses >= 4:
            deviation = statistics.mean([abs(s.total_calories - goal_calories) for s in daily_summaries])
            alert = self._create_alert(
                user_id=user_id,
                alert_type='goal_deviation',
                severity='medium',
                title='Calorie Goal Adherence Issue',
                message=f'You\'ve missed your calorie goal for {calorie_misses} days with an average deviation of {deviation:.0f} calories.',
                data_context={
                    'goal_calories': goal_calories,
                    'missed_days': calorie_misses,
                    'avg_deviation': round(deviation, 1),
                    'suggestions': ['Track meals more carefully', 'Plan meals in advance', 'Use smaller plates for portion control']
                }
            )
            alerts.append(alert)
        
        if protein_misses >= 4:
            avg_protein = statistics.mean([s.total_protein for s in daily_summaries])
            alert = self._create_alert(
                user_id=user_id,
                alert_type='goal_deviation',
                severity='medium',
                title='Protein Goal Not Being Met',
                message=f'You\'ve missed your protein goal for {protein_misses} days. Average intake: {avg_protein:.1f}g vs goal: {goal_protein}g.',
                data_context={
                    'goal_protein': goal_protein,
                    'avg_protein': round(avg_protein, 1),
                    'missed_days': protein_misses,
                    'suggestions': ['Add dal to every meal', 'Include paneer or curd', 'Snack on nuts and seeds']
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _assess_health_risks(
        self, 
        user_id: int, 
        recent_meals: List[Meal], 
        daily_summaries: List[DailySummary]
    ) -> List[Dict[str, Any]]:
        """Assess potential health risks based on eating patterns"""
        alerts = []
        
        if not daily_summaries:
            return alerts
        
        # 1. Diabetes risk assessment (high carb, low fiber pattern)
        high_carb_days = len([s for s in daily_summaries if s.total_carbs > 300])
        if high_carb_days >= 5:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='health_risk',
                severity='high',
                title='High Carbohydrate Intake Risk',
                message='Consistently high carbohydrate intake may increase diabetes risk. Consider reducing refined carbs and adding fiber.',
                data_context={
                    'high_carb_days': high_carb_days,
                    'avg_carbs': round(statistics.mean([s.total_carbs for s in daily_summaries]), 1),
                    'risk_factors': ['High refined carb intake', 'Potential blood sugar spikes'],
                    'recommendations': ['Choose brown rice over white', 'Add more vegetables', 'Include whole grains']
                }
            )
            alerts.append(alert)
        
        # 2. Cardiovascular risk (high calorie, high fat pattern)
        high_calorie_high_fat_days = len([
            s for s in daily_summaries 
            if s.total_calories > 2500 and s.total_fat > 80
        ])
        if high_calorie_high_fat_days >= 4:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='health_risk',
                severity='high',
                title='Cardiovascular Risk Pattern',
                message='High calorie and fat intake pattern detected. This may increase cardiovascular risk.',
                data_context={
                    'concerning_days': high_calorie_high_fat_days,
                    'avg_calories': round(statistics.mean([s.total_calories for s in daily_summaries]), 1),
                    'avg_fat': round(statistics.mean([s.total_fat for s in daily_summaries]), 1),
                    'recommendations': ['Use less oil in cooking', 'Choose lean proteins', 'Increase physical activity']
                }
            )
            alerts.append(alert)
        
        # 3. Nutritional deficiency risk (very low calorie pattern)
        very_low_calorie_days = len([s for s in daily_summaries if s.total_calories < 1200])
        if very_low_calorie_days >= 3:
            alert = self._create_alert(
                user_id=user_id,
                alert_type='health_risk',
                severity='high',
                title='Potential Nutritional Deficiency Risk',
                message=f'Very low calorie intake for {very_low_calorie_days} days may lead to nutritional deficiencies.',
                data_context={
                    'low_calorie_days': very_low_calorie_days,
                    'min_calories': min([s.total_calories for s in daily_summaries]),
                    'recommendations': ['Ensure adequate calorie intake', 'Include nutrient-dense foods', 'Consider consulting a nutritionist']
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _update_behavior_patterns(
        self, 
        user_id: int, 
        recent_meals: List[Meal], 
        daily_summaries: List[DailySummary]
    ) -> List[Dict[str, Any]]:
        """Update user behavior patterns for predictive analytics"""
        patterns_updated = []
        
        try:
            # 1. Eating time patterns
            eating_times = [m.upload_time.hour for m in recent_meals if m.upload_time]
            if eating_times:
                time_pattern = self._analyze_eating_time_pattern(eating_times)
                self._update_pattern(user_id, 'eating_time', time_pattern)
                patterns_updated.append({'type': 'eating_time', 'data': time_pattern})
            
            # 2. Food preference patterns
            food_preferences = self._analyze_food_preferences(recent_meals)
            self._update_pattern(user_id, 'food_preference', food_preferences)
            patterns_updated.append({'type': 'food_preference', 'data': food_preferences})
            
            # 3. Calorie trend patterns
            if daily_summaries:
                calorie_trend = self._analyze_calorie_trend(daily_summaries)
                self._update_pattern(user_id, 'calorie_trend', calorie_trend)
                patterns_updated.append({'type': 'calorie_trend', 'data': calorie_trend})
            
            # 4. Macro balance patterns
            if daily_summaries:
                macro_balance = self._analyze_macro_balance(daily_summaries)
                self._update_pattern(user_id, 'macro_balance', macro_balance)
                patterns_updated.append({'type': 'macro_balance', 'data': macro_balance})
            
            return patterns_updated
            
        except Exception as e:
            print(f"Error updating behavior patterns: {e}")
            return patterns_updated
    
    def _generate_predictive_insights(
        self, 
        user_id: int, 
        recent_meals: List[Meal], 
        daily_summaries: List[DailySummary]
    ) -> List[Dict[str, Any]]:
        """Generate predictive insights about user's health trajectory"""
        insights = []
        
        if len(daily_summaries) < 7:
            return insights
        
        try:
            # 1. Weight trend prediction (based on calorie patterns)
            calorie_trend = self._predict_weight_trend(daily_summaries)
            if calorie_trend['prediction'] != 'stable':
                insight = self._create_insight(
                    user_id=user_id,
                    insight_type='health_prediction',
                    title=f'Weight Trend Prediction: {calorie_trend["prediction"].title()}',
                    description=calorie_trend['description'],
                    prediction_data=calorie_trend,
                    confidence_level=calorie_trend['confidence'],
                    time_horizon='medium_term'
                )
                insights.append(insight)
            
            # 2. Goal achievement prediction
            goal_prediction = self._predict_goal_achievement(user_id, daily_summaries)
            if goal_prediction:
                insight = self._create_insight(
                    user_id=user_id,
                    insight_type='goal_prediction',
                    title='Goal Achievement Forecast',
                    description=goal_prediction['description'],
                    prediction_data=goal_prediction,
                    confidence_level=goal_prediction['confidence'],
                    time_horizon='short_term'
                )
                insights.append(insight)
            
            # 3. Health risk prediction
            risk_prediction = self._predict_health_risks(daily_summaries)
            if risk_prediction['risk_level'] != 'low':
                insight = self._create_insight(
                    user_id=user_id,
                    insight_type='health_risk',
                    title=f'Health Risk Assessment: {risk_prediction["risk_level"].title()}',
                    description=risk_prediction['description'],
                    prediction_data=risk_prediction,
                    confidence_level=risk_prediction['confidence'],
                    time_horizon='long_term'
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            print(f"Error generating predictive insights: {e}")
            return insights
    
    def get_active_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active alerts for a user"""
        try:
            alerts = self.db.query(HealthAlert).filter(
                and_(
                    HealthAlert.user_id == user_id,
                    HealthAlert.is_dismissed == False,
                    or_(
                        HealthAlert.expires_at.is_(None),
                        HealthAlert.expires_at > datetime.now()
                    )
                )
            ).order_by(
                desc(HealthAlert.severity),
                desc(HealthAlert.triggered_at)
            ).all()
            
            return [
                {
                    'id': alert.id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'data_context': alert.data_context,
                    'is_read': alert.is_read,
                    'triggered_at': alert.triggered_at.isoformat(),
                    'expires_at': alert.expires_at.isoformat() if alert.expires_at else None
                }
                for alert in alerts
            ]
            
        except Exception as e:
            print(f"Error getting active alerts: {e}")
            return []
    
    def dismiss_alert(self, user_id: int, alert_id: int) -> bool:
        """Dismiss a specific alert"""
        try:
            alert = self.db.query(HealthAlert).filter(
                and_(
                    HealthAlert.id == alert_id,
                    HealthAlert.user_id == user_id
                )
            ).first()
            
            if alert:
                alert.is_dismissed = True
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error dismissing alert: {e}")
            self.db.rollback()
            return False
    
    def mark_alert_read(self, user_id: int, alert_id: int) -> bool:
        """Mark an alert as read"""
        try:
            alert = self.db.query(HealthAlert).filter(
                and_(
                    HealthAlert.id == alert_id,
                    HealthAlert.user_id == user_id
                )
            ).first()
            
            if alert:
                alert.is_read = True
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error marking alert as read: {e}")
            self.db.rollback()
            return False
    
    # Helper methods
    def _get_recent_meals(self, user_id: int, days: int = 14) -> List[Meal]:
        """Get recent meals for analysis"""
        cutoff_date = date.today() - timedelta(days=days)
        return self.db.query(Meal).filter(
            and_(
                Meal.user_id == user_id,
                Meal.upload_date >= cutoff_date
            )
        ).order_by(desc(Meal.upload_time)).all()
    
    def _get_recent_summaries(self, user_id: int, days: int = 14) -> List[DailySummary]:
        """Get recent daily summaries for analysis"""
        cutoff_date = date.today() - timedelta(days=days)
        return self.db.query(DailySummary).filter(
            and_(
                DailySummary.user_id == user_id,
                DailySummary.date >= cutoff_date
            )
        ).order_by(desc(DailySummary.date)).all()
    
    def _create_alert(self, **kwargs) -> Dict[str, Any]:
        """Create and store a health alert"""
        try:
            # Set expiration time based on alert type
            expires_at = None
            if kwargs['alert_type'] in ['nutrition_gap', 'pattern_concern']:
                expires_at = datetime.now() + timedelta(days=7)
            elif kwargs['alert_type'] == 'goal_deviation':
                expires_at = datetime.now() + timedelta(days=3)
            elif kwargs['alert_type'] == 'health_risk':
                expires_at = datetime.now() + timedelta(days=14)
            
            alert = HealthAlert(
                user_id=kwargs['user_id'],
                alert_type=kwargs['alert_type'],
                severity=kwargs['severity'],
                title=kwargs['title'],
                message=kwargs['message'],
                data_context=kwargs.get('data_context', {}),
                expires_at=expires_at
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            return {
                'id': alert.id,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'data_context': alert.data_context,
                'triggered_at': alert.triggered_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error creating alert: {e}")
            self.db.rollback()
            return {}
    
    def _create_insight(self, **kwargs) -> Dict[str, Any]:
        """Create and store a predictive insight"""
        try:
            # Set expiration based on time horizon
            expires_at = datetime.now() + timedelta(days=30)
            if kwargs['time_horizon'] == 'short_term':
                expires_at = datetime.now() + timedelta(days=7)
            elif kwargs['time_horizon'] == 'long_term':
                expires_at = datetime.now() + timedelta(days=90)
            
            insight = PredictiveInsight(
                user_id=kwargs['user_id'],
                insight_type=kwargs['insight_type'],
                title=kwargs['title'],
                description=kwargs['description'],
                prediction_data=kwargs.get('prediction_data', {}),
                confidence_level=kwargs.get('confidence_level', 0.5),
                time_horizon=kwargs['time_horizon'],
                actionable_recommendations=kwargs.get('actionable_recommendations', []),
                expires_at=expires_at
            )
            
            self.db.add(insight)
            self.db.commit()
            self.db.refresh(insight)
            
            return {
                'id': insight.id,
                'insight_type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'prediction_data': insight.prediction_data,
                'confidence_level': insight.confidence_level,
                'time_horizon': insight.time_horizon,
                'created_at': insight.created_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error creating insight: {e}")
            self.db.rollback()
            return {}
    
    def _analyze_food_variety(self, meals: List[Meal]) -> Dict[str, Any]:
        """Analyze food variety in recent meals"""
        all_foods = set()
        food_counts = {}
        
        for meal in meals:
            if meal.analysis_data and meal.analysis_data.get('items'):
                for item in meal.analysis_data['items']:
                    food_name = item.get('name', '').lower()
                    if food_name:
                        all_foods.add(food_name)
                        food_counts[food_name] = food_counts.get(food_name, 0) + 1
        
        most_common = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'unique_foods': len(all_foods),
            'most_common': [{'food': food, 'count': count} for food, count in most_common],
            'variety_score': min(len(all_foods) / 20, 1.0)  # Score out of 1.0
        }
    
    def _analyze_eating_time_pattern(self, eating_times: List[int]) -> Dict[str, Any]:
        """Analyze eating time patterns"""
        if not eating_times:
            return {}
        
        breakfast_times = [t for t in eating_times if 5 <= t <= 11]
        lunch_times = [t for t in eating_times if 11 < t <= 16]
        dinner_times = [t for t in eating_times if 16 < t <= 23]
        
        return {
            'avg_breakfast_time': statistics.mean(breakfast_times) if breakfast_times else None,
            'avg_lunch_time': statistics.mean(lunch_times) if lunch_times else None,
            'avg_dinner_time': statistics.mean(dinner_times) if dinner_times else None,
            'eating_window': max(eating_times) - min(eating_times) if eating_times else 0,
            'meal_frequency': len(eating_times),
            'late_meals': len([t for t in eating_times if t >= 21])
        }
    
    def _analyze_food_preferences(self, meals: List[Meal]) -> Dict[str, Any]:
        """Analyze food preferences from meal history"""
        cuisine_types = {}
        cooking_methods = {}
        ingredients = {}
        
        for meal in meals:
            if meal.analysis_data and meal.analysis_data.get('items'):
                for item in meal.analysis_data['items']:
                    food_name = item.get('name', '').lower()
                    
                    # Simple cuisine classification
                    if any(word in food_name for word in ['dal', 'curry', 'rice', 'roti', 'sabzi']):
                        cuisine_types['indian'] = cuisine_types.get('indian', 0) + 1
                    elif any(word in food_name for word in ['pasta', 'pizza', 'bread']):
                        cuisine_types['western'] = cuisine_types.get('western', 0) + 1
                    elif any(word in food_name for word in ['noodles', 'fried rice']):
                        cuisine_types['chinese'] = cuisine_types.get('chinese', 0) + 1
                    
                    # Cooking methods
                    if any(word in food_name for word in ['fried', 'fry']):
                        cooking_methods['fried'] = cooking_methods.get('fried', 0) + 1
                    elif any(word in food_name for word in ['steamed', 'boiled']):
                        cooking_methods['steamed'] = cooking_methods.get('steamed', 0) + 1
                    elif any(word in food_name for word in ['grilled', 'roasted']):
                        cooking_methods['grilled'] = cooking_methods.get('grilled', 0) + 1
        
        return {
            'cuisine_preferences': cuisine_types,
            'cooking_methods': cooking_methods,
            'total_meals_analyzed': len(meals)
        }
    
    def _analyze_calorie_trend(self, daily_summaries: List[DailySummary]) -> Dict[str, Any]:
        """Analyze calorie intake trends"""
        if len(daily_summaries) < 3:
            return {}
        
        calories = [s.total_calories for s in daily_summaries if s.total_calories > 0]
        if not calories:
            return {}
        
        # Calculate trend
        avg_calories = statistics.mean(calories)
        recent_avg = statistics.mean(calories[:3]) if len(calories) >= 3 else avg_calories
        older_avg = statistics.mean(calories[3:]) if len(calories) > 3 else avg_calories
        
        trend = 'stable'
        if recent_avg > older_avg + 200:
            trend = 'increasing'
        elif recent_avg < older_avg - 200:
            trend = 'decreasing'
        
        return {
            'avg_calories': round(avg_calories, 1),
            'recent_avg': round(recent_avg, 1),
            'trend': trend,
            'variability': round(statistics.stdev(calories) if len(calories) > 1 else 0, 1),
            'max_calories': max(calories),
            'min_calories': min(calories)
        }
    
    def _analyze_macro_balance(self, daily_summaries: List[DailySummary]) -> Dict[str, Any]:
        """Analyze macronutrient balance patterns"""
        if not daily_summaries:
            return {}
        
        protein_ratios = []
        carb_ratios = []
        fat_ratios = []
        
        for summary in daily_summaries:
            if summary.total_calories > 0:
                protein_ratio = (summary.total_protein * 4 / summary.total_calories) * 100
                carb_ratio = (summary.total_carbs * 4 / summary.total_calories) * 100
                fat_ratio = (summary.total_fat * 9 / summary.total_calories) * 100
                
                protein_ratios.append(protein_ratio)
                carb_ratios.append(carb_ratio)
                fat_ratios.append(fat_ratio)
        
        if not protein_ratios:
            return {}
        
        return {
            'avg_protein_percent': round(statistics.mean(protein_ratios), 1),
            'avg_carb_percent': round(statistics.mean(carb_ratios), 1),
            'avg_fat_percent': round(statistics.mean(fat_ratios), 1),
            'protein_consistency': round(statistics.stdev(protein_ratios) if len(protein_ratios) > 1 else 0, 1),
            'balance_score': self._calculate_balance_score(protein_ratios, carb_ratios, fat_ratios)
        }
    
    def _calculate_balance_score(self, protein_ratios: List[float], carb_ratios: List[float], fat_ratios: List[float]) -> float:
        """Calculate a balance score for macronutrients (0-1)"""
        if not protein_ratios:
            return 0.0
        
        avg_protein = statistics.mean(protein_ratios)
        avg_carb = statistics.mean(carb_ratios)
        avg_fat = statistics.mean(fat_ratios)
        
        # Ideal ranges: Protein 15-25%, Carbs 45-65%, Fat 20-35%
        protein_score = 1.0 if 15 <= avg_protein <= 25 else max(0, 1 - abs(avg_protein - 20) / 20)
        carb_score = 1.0 if 45 <= avg_carb <= 65 else max(0, 1 - abs(avg_carb - 55) / 30)
        fat_score = 1.0 if 20 <= avg_fat <= 35 else max(0, 1 - abs(avg_fat - 27.5) / 15)
        
        return round((protein_score + carb_score + fat_score) / 3, 2)
    
    def _update_pattern(self, user_id: int, pattern_type: str, pattern_data: Dict[str, Any]):
        """Update or create a behavior pattern"""
        try:
            existing_pattern = self.db.query(UserBehaviorPattern).filter(
                and_(
                    UserBehaviorPattern.user_id == user_id,
                    UserBehaviorPattern.pattern_type == pattern_type
                )
            ).first()
            
            confidence_score = self._calculate_pattern_confidence(pattern_data)
            
            if existing_pattern:
                existing_pattern.pattern_data = pattern_data
                existing_pattern.confidence_score = confidence_score
                existing_pattern.last_updated = datetime.now()
            else:
                new_pattern = UserBehaviorPattern(
                    user_id=user_id,
                    pattern_type=pattern_type,
                    pattern_data=pattern_data,
                    confidence_score=confidence_score
                )
                self.db.add(new_pattern)
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating pattern: {e}")
            self.db.rollback()
    
    def _calculate_pattern_confidence(self, pattern_data: Dict[str, Any]) -> float:
        """Calculate confidence score for a pattern based on data quality"""
        if not pattern_data:
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on data completeness
        if pattern_data.get('total_meals_analyzed', 0) > 10:
            confidence += 0.2
        if pattern_data.get('variability', 0) < 50:  # Low variability = more consistent pattern
            confidence += 0.2
        if len(pattern_data) > 3:  # More data points
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _predict_weight_trend(self, daily_summaries: List[DailySummary]) -> Dict[str, Any]:
        """Predict weight trend based on calorie patterns"""
        if len(daily_summaries) < 7:
            return {'prediction': 'stable', 'confidence': 0.0}
        
        calories = [s.total_calories for s in daily_summaries if s.total_calories > 0]
        if not calories:
            return {'prediction': 'stable', 'confidence': 0.0}
        
        avg_calories = statistics.mean(calories)
        
        # Simple prediction based on average calorie intake
        # Assuming maintenance calories around 2000-2200 for average person
        maintenance_calories = 2100
        
        prediction = 'stable'
        confidence = 0.6
        description = ""
        
        if avg_calories > maintenance_calories + 300:
            prediction = 'weight_gain'
            description = f"Based on your average intake of {avg_calories:.0f} calories, you may experience gradual weight gain."
            confidence = 0.7
        elif avg_calories < maintenance_calories - 300:
            prediction = 'weight_loss'
            description = f"Based on your average intake of {avg_calories:.0f} calories, you may experience gradual weight loss."
            confidence = 0.7
        else:
            description = f"Your average intake of {avg_calories:.0f} calories suggests stable weight maintenance."
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'description': description,
            'avg_calories': round(avg_calories, 1),
            'maintenance_estimate': maintenance_calories,
            'calorie_surplus_deficit': round(avg_calories - maintenance_calories, 1)
        }
    
    def _predict_goal_achievement(self, user_id: int, daily_summaries: List[DailySummary]) -> Optional[Dict[str, Any]]:
        """Predict goal achievement based on current patterns"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.daily_goals or not daily_summaries:
            return None
        
        goal_calories = user.daily_goals.get('calories', 2000)
        goal_protein = user.daily_goals.get('protein', 60)
        
        # Calculate adherence rates
        calorie_adherence = len([s for s in daily_summaries if abs(s.total_calories - goal_calories) <= 200]) / len(daily_summaries)
        protein_adherence = len([s for s in daily_summaries if s.total_protein >= goal_protein * 0.8]) / len(daily_summaries)
        
        overall_adherence = (calorie_adherence + protein_adherence) / 2
        
        if overall_adherence >= 0.8:
            prediction = 'likely_to_achieve'
            description = f"You're on track! {overall_adherence*100:.0f}% adherence to your goals."
        elif overall_adherence >= 0.6:
            prediction = 'moderate_progress'
            description = f"Good progress with {overall_adherence*100:.0f}% adherence. Small adjustments could help."
        else:
            prediction = 'needs_improvement'
            description = f"Goal adherence is {overall_adherence*100:.0f}%. Consider reviewing your approach."
        
        return {
            'prediction': prediction,
            'confidence': min(0.8, overall_adherence + 0.2),
            'description': description,
            'calorie_adherence': round(calorie_adherence * 100, 1),
            'protein_adherence': round(protein_adherence * 100, 1),
            'overall_adherence': round(overall_adherence * 100, 1)
        }
    
    def _predict_health_risks(self, daily_summaries: List[DailySummary]) -> Dict[str, Any]:
        """Predict potential health risks based on eating patterns"""
        if not daily_summaries:
            return {'risk_level': 'low', 'confidence': 0.0}
        
        risk_factors = []
        risk_score = 0
        
        # Calculate averages
        avg_calories = statistics.mean([s.total_calories for s in daily_summaries if s.total_calories > 0])
        avg_carbs = statistics.mean([s.total_carbs for s in daily_summaries if s.total_carbs > 0])
        avg_fat = statistics.mean([s.total_fat for s in daily_summaries if s.total_fat > 0])
        
        # Risk factor analysis
        if avg_calories > 2500:
            risk_factors.append('High calorie intake')
            risk_score += 1
        
        if avg_carbs > 300:
            risk_factors.append('High carbohydrate intake')
            risk_score += 1
        
        if avg_fat > 80:
            risk_factors.append('High fat intake')
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 2:
            risk_level = 'high'
            description = f"Multiple risk factors detected: {', '.join(risk_factors)}. Consider dietary adjustments."
        elif risk_score == 1:
            risk_level = 'medium'
            description = f"Some concern: {', '.join(risk_factors)}. Monitor and consider moderation."
        else:
            risk_level = 'low'
            description = "Current eating patterns show low health risk indicators."
        
        return {
            'risk_level': risk_level,
            'confidence': 0.6 + (len(daily_summaries) / 20),  # Higher confidence with more data
            'description': description,
            'risk_factors': risk_factors,
            'risk_score': risk_score
        }
