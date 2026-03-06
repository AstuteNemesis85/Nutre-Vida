from datetime import datetime, timedelta, time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.models.agentic_models import SmartNotification, UserBehaviorPattern
from app.models.db_models import User, Meal
import json
import statistics

class SmartNotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_types = {
            'meal_reminder': {
                'default_message': 'Time for your {meal_type}! Based on your usual pattern.',
                'priority': 'medium'
            },
            'hydration': {
                'default_message': 'Stay hydrated! Remember to drink water throughout the day.',
                'priority': 'low'
            },
            'goal_check': {
                'default_message': 'How are you doing with your daily goals? Check your progress!',
                'priority': 'medium'
            },
            'health_tip': {
                'default_message': 'Here\'s a personalized health tip for you!',
                'priority': 'low'
            },
            'meal_planning': {
                'default_message': 'Time to plan your meals for tomorrow!',
                'priority': 'medium'
            }
        }
    
    def generate_smart_notifications(self, user_id: int) -> Dict[str, Any]:
        """Generate personalized smart notifications for a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            # Get user behavior patterns
            patterns = self._get_user_patterns(user_id)
            recent_meals = self._get_recent_meals(user_id, days=7)
            
            notifications_created = []
            
            # 1. Generate meal reminder notifications
            meal_reminders = self._generate_meal_reminders(user_id, patterns, recent_meals)
            notifications_created.extend(meal_reminders)
            
            # 2. Generate hydration reminders
            hydration_reminders = self._generate_hydration_reminders(user_id, patterns)
            notifications_created.extend(hydration_reminders)
            
            # 3. Generate goal check notifications
            goal_reminders = self._generate_goal_check_reminders(user_id, user.daily_goals)
            notifications_created.extend(goal_reminders)
            
            # 4. Generate health tip notifications
            health_tips = self._generate_health_tip_notifications(user_id, patterns)
            notifications_created.extend(health_tips)
            
            # 5. Generate meal planning reminders
            planning_reminders = self._generate_meal_planning_reminders(user_id, patterns)
            notifications_created.extend(planning_reminders)
            
            return {
                'notifications_generated': len(notifications_created),
                'notifications': notifications_created,
                'generation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating smart notifications: {e}")
            return {'error': str(e)}
    
    def _generate_meal_reminders(
        self, 
        user_id: int, 
        patterns: Dict[str, Any], 
        recent_meals: List[Meal]
    ) -> List[Dict[str, Any]]:
        """Generate personalized meal reminder notifications"""
        notifications = []
        
        # Get eating time patterns
        eating_pattern = patterns.get('eating_time', {})
        if not eating_pattern:
            # Use default meal times if no pattern exists
            eating_pattern = {
                'avg_breakfast_time': 8.0,
                'avg_lunch_time': 13.0,
                'avg_dinner_time': 19.0
            }
        
        # Generate reminders for next 3 days
        for day_offset in range(1, 4):
            target_date = datetime.now() + timedelta(days=day_offset)
            
            # Breakfast reminder
            if eating_pattern.get('avg_breakfast_time'):
                breakfast_time = self._calculate_optimal_reminder_time(
                    eating_pattern['avg_breakfast_time'], 
                    'breakfast'
                )
                breakfast_datetime = target_date.replace(
                    hour=int(breakfast_time), 
                    minute=int((breakfast_time % 1) * 60),
                    second=0,
                    microsecond=0
                )
                
                # Only create if it's in the future
                if breakfast_datetime > datetime.now():
                    notification = self._create_notification(
                        user_id=user_id,
                        notification_type='meal_reminder',
                        title='Breakfast Reminder',
                        message=self._personalize_meal_message('breakfast', patterns, recent_meals),
                        scheduled_time=breakfast_datetime,
                        personalization_data={
                            'meal_type': 'breakfast',
                            'usual_time': eating_pattern['avg_breakfast_time'],
                            'suggestions': self._get_meal_suggestions('breakfast', patterns)
                        }
                    )
                    if notification:
                        notifications.append(notification)
            
            # Lunch reminder
            if eating_pattern.get('avg_lunch_time'):
                lunch_time = self._calculate_optimal_reminder_time(
                    eating_pattern['avg_lunch_time'], 
                    'lunch'
                )
                lunch_datetime = target_date.replace(
                    hour=int(lunch_time), 
                    minute=int((lunch_time % 1) * 60),
                    second=0,
                    microsecond=0
                )
                
                if lunch_datetime > datetime.now():
                    notification = self._create_notification(
                        user_id=user_id,
                        notification_type='meal_reminder',
                        title='Lunch Reminder',
                        message=self._personalize_meal_message('lunch', patterns, recent_meals),
                        scheduled_time=lunch_datetime,
                        personalization_data={
                            'meal_type': 'lunch',
                            'usual_time': eating_pattern['avg_lunch_time'],
                            'suggestions': self._get_meal_suggestions('lunch', patterns)
                        }
                    )
                    if notification:
                        notifications.append(notification)
            
            # Dinner reminder
            if eating_pattern.get('avg_dinner_time'):
                dinner_time = self._calculate_optimal_reminder_time(
                    eating_pattern['avg_dinner_time'], 
                    'dinner'
                )
                dinner_datetime = target_date.replace(
                    hour=int(dinner_time), 
                    minute=int((dinner_time % 1) * 60),
                    second=0,
                    microsecond=0
                )
                
                if dinner_datetime > datetime.now():
                    notification = self._create_notification(
                        user_id=user_id,
                        notification_type='meal_reminder',
                        title='Dinner Reminder',
                        message=self._personalize_meal_message('dinner', patterns, recent_meals),
                        scheduled_time=dinner_datetime,
                        personalization_data={
                            'meal_type': 'dinner',
                            'usual_time': eating_pattern['avg_dinner_time'],
                            'suggestions': self._get_meal_suggestions('dinner', patterns)
                        }
                    )
                    if notification:
                        notifications.append(notification)
        
        return notifications
    
    def _generate_hydration_reminders(
        self, 
        user_id: int, 
        patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hydration reminder notifications"""
        notifications = []
        
        # Generate hydration reminders for the next day
        tomorrow = datetime.now() + timedelta(days=1)
        
        # Morning hydration reminder
        morning_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        if morning_time > datetime.now():
            notification = self._create_notification(
                user_id=user_id,
                notification_type='hydration',
                title='Morning Hydration',
                message='Start your day right! Have a glass of warm water with lemon to kickstart your metabolism. 🌅💧',
                scheduled_time=morning_time,
                is_recurring=True,
                recurrence_pattern={'type': 'daily', 'time': '09:00'},
                personalization_data={
                    'hydration_type': 'morning',
                    'suggestions': ['Warm water with lemon', 'Herbal tea', 'Plain water']
                }
            )
            if notification:
                notifications.append(notification)
        
        # Afternoon hydration reminder
        afternoon_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        if afternoon_time > datetime.now():
            notification = self._create_notification(
                user_id=user_id,
                notification_type='hydration',
                title='Afternoon Hydration Check',
                message='Feeling tired? You might need water! Stay hydrated to maintain energy levels. 💪💧',
                scheduled_time=afternoon_time,
                is_recurring=True,
                recurrence_pattern={'type': 'daily', 'time': '15:00'},
                personalization_data={
                    'hydration_type': 'afternoon',
                    'suggestions': ['Plain water', 'Buttermilk', 'Coconut water', 'Herbal tea']
                }
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def _generate_goal_check_reminders(
        self, 
        user_id: int, 
        daily_goals: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate goal check reminder notifications"""
        notifications = []
        
        if not daily_goals:
            return notifications
        
        # Evening goal check reminder
        tomorrow = datetime.now() + timedelta(days=1)
        evening_time = tomorrow.replace(hour=20, minute=0, second=0, microsecond=0)
        
        if evening_time > datetime.now():
            notification = self._create_notification(
                user_id=user_id,
                notification_type='goal_check',
                title='Daily Goal Check-in',
                message=f'How did you do today? Check if you met your {daily_goals.get("calories", 2000)} calorie and {daily_goals.get("protein", 60)}g protein goals! 🎯',
                scheduled_time=evening_time,
                is_recurring=True,
                recurrence_pattern={'type': 'daily', 'time': '20:00'},
                personalization_data={
                    'goal_calories': daily_goals.get('calories', 2000),
                    'goal_protein': daily_goals.get('protein', 60),
                    'check_type': 'daily_summary'
                }
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def _generate_health_tip_notifications(
        self, 
        user_id: int, 
        patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized health tip notifications"""
        notifications = []
        
        # Generate health tips based on user patterns
        tips = self._get_personalized_health_tips(patterns)
        
        # Schedule one tip for tomorrow morning
        tomorrow = datetime.now() + timedelta(days=1)
        tip_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        if tip_time > datetime.now() and tips:
            selected_tip = tips[0]  # Use the first (most relevant) tip
            
            notification = self._create_notification(
                user_id=user_id,
                notification_type='health_tip',
                title='Daily Health Tip',
                message=selected_tip['message'],
                scheduled_time=tip_time,
                personalization_data={
                    'tip_category': selected_tip['category'],
                    'relevance_reason': selected_tip['reason'],
                    'actionable': True
                }
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def _generate_meal_planning_reminders(
        self, 
        user_id: int, 
        patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate meal planning reminder notifications"""
        notifications = []
        
        # Evening meal planning reminder for next day
        today = datetime.now()
        planning_time = today.replace(hour=21, minute=30, second=0, microsecond=0)
        
        # Only create if it's still today and in the future
        if planning_time > datetime.now() and planning_time.date() == today.date():
            notification = self._create_notification(
                user_id=user_id,
                notification_type='meal_planning',
                title='Plan Tomorrow\'s Meals',
                message='Take 5 minutes to plan tomorrow\'s meals! It helps you stay on track with your health goals. 📝🍽️',
                scheduled_time=planning_time,
                is_recurring=True,
                recurrence_pattern={'type': 'daily', 'time': '21:30'},
                personalization_data={
                    'planning_type': 'next_day',
                    'suggestions': self._get_planning_suggestions(patterns)
                }
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def get_pending_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all pending notifications for a user"""
        try:
            notifications = self.db.query(SmartNotification).filter(
                and_(
                    SmartNotification.user_id == user_id,
                    SmartNotification.is_sent == False,
                    SmartNotification.scheduled_time <= datetime.now() + timedelta(hours=24)
                )
            ).order_by(SmartNotification.scheduled_time).all()
            
            return [
                {
                    'id': notif.id,
                    'notification_type': notif.notification_type,
                    'title': notif.title,
                    'message': notif.message,
                    'scheduled_time': notif.scheduled_time.isoformat(),
                    'is_recurring': notif.is_recurring,
                    'personalization_data': notif.personalization_data,
                    'created_at': notif.created_at.isoformat()
                }
                for notif in notifications
            ]
            
        except Exception as e:
            print(f"Error getting pending notifications: {e}")
            return []
    
    def mark_notification_sent(self, notification_id: int) -> bool:
        """Mark a notification as sent"""
        try:
            notification = self.db.query(SmartNotification).filter(
                SmartNotification.id == notification_id
            ).first()
            
            if notification:
                notification.is_sent = True
                notification.sent_at = datetime.now()
                
                # If it's recurring, create the next occurrence
                if notification.is_recurring and notification.recurrence_pattern:
                    self._create_recurring_notification(notification)
                
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error marking notification as sent: {e}")
            self.db.rollback()
            return False
    
    def _create_recurring_notification(self, original_notification: SmartNotification):
        """Create the next occurrence of a recurring notification"""
        try:
            recurrence = original_notification.recurrence_pattern
            if recurrence.get('type') == 'daily':
                # Schedule for next day
                next_time = original_notification.scheduled_time + timedelta(days=1)
                
                new_notification = SmartNotification(
                    user_id=original_notification.user_id,
                    notification_type=original_notification.notification_type,
                    title=original_notification.title,
                    message=original_notification.message,
                    scheduled_time=next_time,
                    is_recurring=True,
                    recurrence_pattern=original_notification.recurrence_pattern,
                    personalization_data=original_notification.personalization_data
                )
                
                self.db.add(new_notification)
                self.db.commit()
                
        except Exception as e:
            print(f"Error creating recurring notification: {e}")
            self.db.rollback()
    
    def cleanup_old_notifications(self, days_old: int = 7):
        """Clean up old sent notifications"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_notifications = self.db.query(SmartNotification).filter(
                and_(
                    SmartNotification.is_sent == True,
                    SmartNotification.sent_at < cutoff_date
                )
            ).all()
            
            for notification in old_notifications:
                self.db.delete(notification)
            
            self.db.commit()
            return len(old_notifications)
            
        except Exception as e:
            print(f"Error cleaning up notifications: {e}")
            self.db.rollback()
            return 0
    
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
    
    def _get_recent_meals(self, user_id: int, days: int = 7) -> List[Meal]:
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
    
    def _calculate_optimal_reminder_time(self, usual_meal_time: float, meal_type: str) -> float:
        """Calculate optimal reminder time based on meal type and usual eating time"""
        # Remind 30 minutes before usual time for main meals
        if meal_type in ['breakfast', 'lunch', 'dinner']:
            reminder_time = usual_meal_time - 0.5  # 30 minutes before
        else:
            reminder_time = usual_meal_time - 0.25  # 15 minutes before for snacks
        
        # Ensure reminder time is reasonable (not too early or late)
        if meal_type == 'breakfast':
            reminder_time = max(6.0, min(reminder_time, 11.0))
        elif meal_type == 'lunch':
            reminder_time = max(11.0, min(reminder_time, 16.0))
        elif meal_type == 'dinner':
            reminder_time = max(17.0, min(reminder_time, 22.0))
        
        return reminder_time
    
    def _personalize_meal_message(
        self, 
        meal_type: str, 
        patterns: Dict[str, Any], 
        recent_meals: List[Meal]
    ) -> str:
        """Create personalized meal reminder message"""
        base_messages = {
            'breakfast': [
                "Good morning! Time to fuel your day with a healthy breakfast! 🌅",
                "Rise and shine! Your body needs breakfast to kickstart the metabolism! ☀️",
                "Morning fuel time! Start your day with nutritious breakfast! 🥣"
            ],
            'lunch': [
                "Lunch time! Keep your energy levels up with a balanced meal! 🍽️",
                "Midday refuel! Time for a nutritious lunch to power through the day! 💪",
                "Lunch break! Give your body the nutrients it needs! 🥗"
            ],
            'dinner': [
                "Dinner time! End your day with a satisfying, healthy meal! 🌙",
                "Evening nourishment! Time for a balanced dinner! 🍽️",
                "Dinner's ready! Wrap up your day with good nutrition! ✨"
            ]
        }
        
        # Get base message
        import random
        base_message = random.choice(base_messages.get(meal_type, ["Time for your meal!"]))
        
        # Add personalization based on patterns
        food_preferences = patterns.get('food_preference', {})
        if food_preferences.get('cuisine_preferences'):
            top_cuisine = max(food_preferences['cuisine_preferences'].items(), key=lambda x: x[1])[0]
            if top_cuisine == 'indian':
                base_message += f" How about some traditional {meal_type} today?"
        
        return base_message
    
    def _get_meal_suggestions(self, meal_type: str, patterns: Dict[str, Any]) -> List[str]:
        """Get meal suggestions based on user patterns and meal type"""
        suggestions = {
            'breakfast': [
                'Oats with fruits and nuts',
                'Idli with sambar',
                'Poha with vegetables',
                'Upma with curry leaves',
                'Dosa with coconut chutney',
                'Paratha with curd'
            ],
            'lunch': [
                'Dal rice with vegetables',
                'Roti with sabzi and dal',
                'Quinoa salad with paneer',
                'Rajma rice',
                'Curd rice with pickle',
                'Mixed vegetable curry with rice'
            ],
            'dinner': [
                'Light dal with roti',
                'Vegetable soup with bread',
                'Khichdi with ghee',
                'Grilled vegetables with quinoa',
                'Moong dal cheela',
                'Vegetable curry with brown rice'
            ]
        }
        
        base_suggestions = suggestions.get(meal_type, [])
        
        # Personalize based on food preferences
        food_preferences = patterns.get('food_preference', {})
        if food_preferences.get('cuisine_preferences'):
            top_cuisine = max(food_preferences['cuisine_preferences'].items(), key=lambda x: x[1])[0]
            if top_cuisine == 'indian':
                # Keep Indian suggestions at the top
                return base_suggestions[:4]
        
        return base_suggestions[:3]
    
    def _get_personalized_health_tips(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized health tips based on user patterns"""
        tips = []
        
        # Analyze patterns and generate relevant tips
        eating_pattern = patterns.get('eating_time', {})
        food_preferences = patterns.get('food_preference', {})
        calorie_trend = patterns.get('calorie_trend', {})
        
        # Late meal pattern tip
        if eating_pattern.get('late_meals', 0) > 2:
            tips.append({
                'category': 'meal_timing',
                'message': '🕐 Try eating dinner by 8 PM for better digestion and sleep quality. Your body will thank you!',
                'reason': 'User has pattern of late meals'
            })
        
        # High calorie trend tip
        if calorie_trend.get('trend') == 'increasing':
            tips.append({
                'category': 'calorie_management',
                'message': '🥗 Consider adding more vegetables to your meals and reducing portion sizes slightly to maintain healthy calorie levels.',
                'reason': 'User has increasing calorie trend'
            })
        
        # Food variety tip
        if food_preferences.get('total_meals_analyzed', 0) > 10:
            tips.append({
                'category': 'nutrition_variety',
                'message': '🌈 Try adding one new vegetable or fruit to your meals this week for better micronutrient diversity!',
                'reason': 'Encourage food variety'
            })
        
        # Default tips if no specific patterns
        if not tips:
            tips.extend([
                {
                    'category': 'hydration',
                    'message': '💧 Start your day with a glass of warm water with lemon to boost metabolism and aid digestion.',
                    'reason': 'General health tip'
                },
                {
                    'category': 'mindful_eating',
                    'message': '🧘 Practice mindful eating: chew slowly and appreciate the flavors of your food for better digestion.',
                    'reason': 'General wellness tip'
                },
                {
                    'category': 'meal_prep',
                    'message': '📝 Spend 10 minutes planning tomorrow\'s meals to make healthier choices and save time.',
                    'reason': 'General planning tip'
                }
            ])
        
        return tips
    
    def _get_planning_suggestions(self, patterns: Dict[str, Any]) -> List[str]:
        """Get meal planning suggestions based on user patterns"""
        suggestions = [
            'Plan balanced meals with protein, carbs, and vegetables',
            'Prep ingredients in advance to save time',
            'Include variety in your weekly meal plan',
            'Consider your schedule when planning meal times',
            'Keep healthy snacks ready for busy days'
        ]
        
        # Personalize based on patterns
        food_preferences = patterns.get('food_preference', {})
        if food_preferences.get('cuisine_preferences', {}).get('indian', 0) > 5:
            suggestions.insert(0, 'Plan traditional Indian meals with seasonal vegetables')
        
        return suggestions[:3]
    
    def _create_notification(self, **kwargs) -> Optional[Dict[str, Any]]:
        """Create and store a smart notification"""
        try:
            notification = SmartNotification(
                user_id=kwargs['user_id'],
                notification_type=kwargs['notification_type'],
                title=kwargs['title'],
                message=kwargs['message'],
                scheduled_time=kwargs['scheduled_time'],
                is_recurring=kwargs.get('is_recurring', False),
                recurrence_pattern=kwargs.get('recurrence_pattern', {}),
                personalization_data=kwargs.get('personalization_data', {})
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            return {
                'id': notification.id,
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'scheduled_time': notification.scheduled_time.isoformat(),
                'is_recurring': notification.is_recurring,
                'personalization_data': notification.personalization_data,
                'created_at': notification.created_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error creating notification: {e}")
            self.db.rollback()
            return None
