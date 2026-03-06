from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Date, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ConversationMemory(Base):
    """Store contextual conversation memory across sessions"""
    __tablename__ = "conversation_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, index=True)  # To group conversations by session
    message_type = Column(String)  # 'user' or 'agent'
    content = Column(Text)
    context_data = Column(JSON, default={})  # Store meal context, user state, etc.
    embedding_vector = Column(JSON, default={})  # For semantic search (future enhancement)
    importance_score = Column(Float, default=0.0)  # For memory prioritization
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class HealthAlert(Base):
    """Store proactive health monitoring alerts"""
    __tablename__ = "health_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    alert_type = Column(String)  # 'nutrition_gap', 'calorie_excess', 'pattern_concern', 'goal_deviation'
    severity = Column(String)  # 'low', 'medium', 'high', 'critical'
    title = Column(String)
    message = Column(Text)
    data_context = Column(JSON, default={})  # Supporting data for the alert
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # When alert becomes irrelevant
    
    user = relationship("User")

class SmartNotification(Base):
    """Store smart notifications for meal timing and reminders"""
    __tablename__ = "smart_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    notification_type = Column(String)  # 'meal_reminder', 'hydration', 'exercise', 'goal_check'
    title = Column(String)
    message = Column(Text)
    scheduled_time = Column(DateTime(timezone=True))
    is_sent = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, default={})  # For recurring notifications
    personalization_data = Column(JSON, default={})  # User-specific customization
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True))
    
    user = relationship("User")

class MealPlan(Base):
    """Store AI-generated intelligent meal plans"""
    __tablename__ = "meal_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_name = Column(String)
    plan_type = Column(String)  # 'daily', 'weekly', 'custom'
    start_date = Column(Date)
    end_date = Column(Date)
    goals = Column(JSON, default={})  # Nutritional and health goals for this plan
    preferences = Column(JSON, default={})  # User preferences considered
    plan_data = Column(JSON, default={})  # Complete meal plan structure
    generation_context = Column(JSON, default={})  # Context used for generation
    is_active = Column(Boolean, default=True)
    adherence_score = Column(Float, default=0.0)  # How well user follows the plan
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User")
    meal_plan_items = relationship("MealPlanItem", back_populates="meal_plan")

class MealPlanItem(Base):
    """Individual items within a meal plan"""
    __tablename__ = "meal_plan_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"))
    day_of_plan = Column(Integer)  # Day number in the plan (1, 2, 3...)
    meal_type = Column(String)  # 'breakfast', 'lunch', 'dinner', 'snack'
    food_items = Column(JSON, default=[])  # List of food items with quantities
    nutritional_info = Column(JSON, default={})  # Calculated nutrition
    preparation_notes = Column(Text)
    alternatives = Column(JSON, default=[])  # Alternative food options
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime(timezone=True))
    
    meal_plan = relationship("MealPlan", back_populates="meal_plan_items")

class UserBehaviorPattern(Base):
    """Track user behavior patterns for predictive analytics"""
    __tablename__ = "user_behavior_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pattern_type = Column(String)  # 'eating_time', 'food_preference', 'calorie_trend', 'macro_balance'
    pattern_data = Column(JSON, default={})  # Detailed pattern information
    confidence_score = Column(Float, default=0.0)  # How confident we are in this pattern
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class PredictiveInsight(Base):
    """Store AI-generated predictive insights about user health"""
    __tablename__ = "predictive_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    insight_type = Column(String)  # 'health_risk', 'goal_prediction', 'behavior_forecast'
    title = Column(String)
    description = Column(Text)
    prediction_data = Column(JSON, default={})  # Supporting data and probabilities
    confidence_level = Column(Float, default=0.0)  # 0.0 to 1.0
    time_horizon = Column(String)  # 'short_term', 'medium_term', 'long_term'
    actionable_recommendations = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    user = relationship("User")
