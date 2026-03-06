from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Date, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    phone_verified = Column(Boolean, default=False)
    phone_otp = Column(String, nullable=True)  # Temporary OTP storage
    phone_otp_expires = Column(DateTime(timezone=True), nullable=True)
    profile = Column(JSON, default={})
    daily_goals = Column(JSON, default={})  # Daily calorie/macro goals
    notification_preferences = Column(JSON, default={
        "whatsapp_enabled": True,
        "email_enabled": True,
        "reminder_frequency": 5,  # hours
        "daily_summary": True,
        "weekly_summary": True,
        "monthly_summary": True,
        "quiet_hours_start": 22,  # 10 PM
        "quiet_hours_end": 7     # 7 AM
    })
    last_meal_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    meals = relationship("Meal", back_populates="user")
    daily_summaries = relationship("DailySummary", back_populates="user")
    notifications = relationship("NotificationLog", back_populates="user")

class Meal(Base):
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    analysis_data = Column(JSON, default={})
    portion_estimates = Column(JSON, default={})
    nutrition_summary = Column(JSON, default={})
    recommendations = Column(JSON, default={})
    meal_type = Column(String, nullable=True)  # breakfast, lunch, dinner, snack
    upload_date = Column(Date, server_default=func.current_date())
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    day_of_week = Column(String, nullable=True)  # Monday, Tuesday, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="meals")

class DailySummary(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    total_calories = Column(Float, default=0.0)
    total_protein = Column(Float, default=0.0)
    total_carbs = Column(Float, default=0.0)
    total_fat = Column(Float, default=0.0)
    total_fiber = Column(Float, default=0.0)
    meals_count = Column(Integer, default=0)
    goal_calories_achieved = Column(Boolean, default=False)
    goal_protein_achieved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="daily_summaries")

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    notification_type = Column(String, nullable=False)  # reminder, daily_summary, weekly_summary, monthly_summary, pdf_export
    channel = Column(String, nullable=False)  # whatsapp, email, both
    status = Column(String, default="pending")  # pending, sent, failed
    message_content = Column(String, nullable=True)
    twilio_sid = Column(String, nullable=True)  # For WhatsApp message tracking
    error_message = Column(String, nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="notifications")
