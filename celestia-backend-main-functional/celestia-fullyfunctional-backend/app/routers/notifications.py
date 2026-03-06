from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, validator
import re

from app.database import get_db
from app.models.db_models import User
from app.services.notification_service import NotificationService
from app.services.pdf_report_service import PDFReportService
from app.services.scheduler_service import get_scheduler
from app.services.user_service import get_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Simple authentication dependency - replace with proper JWT auth in production
def get_current_user(user_id: int = 1, db: Session = Depends(get_db)) -> User:
    """
    Simple user authentication - replace with proper JWT authentication in production
    For now, defaults to user_id=1 for testing
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# Pydantic models for request/response
class PhoneVerificationRequest(BaseModel):
    phone_number: str
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove any spaces, dashes, or parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        
        # Check if it's a valid international format
        if not re.match(r'^\+[1-9]\d{1,14}$', cleaned):
            raise ValueError('Phone number must be in international format (e.g., +919876543210)')
        
        return cleaned

class OTPVerificationRequest(BaseModel):
    otp: str
    
    @validator('otp')
    def validate_otp(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be exactly 6 digits')
        return v

class NotificationPreferencesRequest(BaseModel):
    whatsapp_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    reminder_frequency: Optional[int] = None
    daily_summary: Optional[bool] = None
    weekly_summary: Optional[bool] = None
    monthly_summary: Optional[bool] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    
    @validator('reminder_frequency')
    def validate_reminder_frequency(cls, v):
        if v is not None and (v < 1 or v > 24):
            raise ValueError('Reminder frequency must be between 1 and 24 hours')
        return v
    
    @validator('quiet_hours_start', 'quiet_hours_end')
    def validate_quiet_hours(cls, v):
        if v is not None and (v < 0 or v > 23):
            raise ValueError('Quiet hours must be between 0 and 23')
        return v

class PDFExportRequest(BaseModel):
    report_type: str = "weekly"
    days_back: Optional[int] = None
    
    @validator('report_type')
    def validate_report_type(cls, v):
        if v not in ['weekly', 'monthly', 'quarterly', 'custom']:
            raise ValueError('Report type must be weekly, monthly, quarterly, or custom')
        return v
    
    @validator('days_back')
    def validate_days_back(cls, v):
        if v is not None and (v < 1 or v > 365):
            raise ValueError('Days back must be between 1 and 365')
        return v

@router.post("/phone/send-otp")
async def send_phone_verification_otp(
    request: PhoneVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send OTP for phone number verification"""
    try:
        notification_service = NotificationService(db)
        
        # Update user's phone number
        current_user.phone_number = request.phone_number
        db.commit()
        
        # Send OTP
        result = notification_service.send_phone_verification_otp(
            user_id=current_user.id,
            phone_number=request.phone_number
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": "OTP sent successfully to your WhatsApp",
                "phone_number": request.phone_number
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send OTP")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending OTP: {str(e)}"
        )

@router.post("/phone/verify-otp")
async def verify_phone_otp(
    request: OTPVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify OTP and mark phone as verified"""
    try:
        notification_service = NotificationService(db)
        
        result = notification_service.verify_phone_otp(
            user_id=current_user.id,
            otp=request.otp
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Phone number verified successfully",
                "phone_verified": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Invalid or expired OTP")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying OTP: {str(e)}"
        )

@router.get("/phone/status")
async def get_phone_verification_status(
    current_user: User = Depends(get_current_user)
):
    """Get current phone verification status"""
    return {
        "phone_number": current_user.phone_number,
        "phone_verified": current_user.phone_verified,
        "has_phone_number": current_user.phone_number is not None
    }

@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get user's notification preferences"""
    preferences = current_user.notification_preferences or {}
    
    # Ensure all default values are present
    default_preferences = {
        "whatsapp_enabled": True,
        "email_enabled": True,
        "reminder_frequency": 5,
        "daily_summary": True,
        "weekly_summary": True,
        "monthly_summary": True,
        "quiet_hours_start": 22,
        "quiet_hours_end": 7
    }
    
    # Merge with defaults
    for key, default_value in default_preferences.items():
        if key not in preferences:
            preferences[key] = default_value
    
    return {
        "preferences": preferences,
        "phone_verified": current_user.phone_verified,
        "email_available": current_user.email is not None
    }

@router.put("/preferences")
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences"""
    try:
        notification_service = NotificationService(db)
        
        # Build preferences update dict
        preferences_update = {}
        
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                preferences_update[field] = value
        
        if not preferences_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preferences provided to update"
            )
        
        result = notification_service.update_notification_preferences(
            user_id=current_user.id,
            preferences=preferences_update
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Notification preferences updated successfully",
                "preferences": result.get("preferences")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update preferences")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preferences: {str(e)}"
        )

@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notification history"""
    try:
        notification_service = NotificationService(db)
        
        history = notification_service.get_notification_history(
            user_id=current_user.id,
            limit=min(limit, 100)  # Cap at 100
        )
        
        return {
            "history": history,
            "total_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting notification history: {str(e)}"
        )

@router.post("/test-reminder")
async def send_test_reminder(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a test meal reminder to the user"""
    try:
        if not current_user.phone_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number must be verified to receive reminders"
            )
        
        scheduler = get_scheduler()
        result = scheduler.send_immediate_reminder(current_user.id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Test reminder sent successfully",
                "message_sid": result.get("message_sid")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send test reminder")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending test reminder: {str(e)}"
        )

@router.post("/export-pdf")
async def export_pdf_report(
    request: PDFExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate and send PDF report via WhatsApp and email"""
    try:
        # Determine days back
        days_back = request.days_back
        if days_back is None:
            days_back = {
                "weekly": 7,
                "monthly": 30,
                "quarterly": 90
            }.get(request.report_type, 7)
        
        # Generate and send report
        scheduler = get_scheduler()
        result = scheduler.generate_and_send_report(
            user_id=current_user.id,
            report_type=request.report_type
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"PDF report generated and sent successfully",
                "report_type": request.report_type,
                "days_covered": days_back,
                "delivery_results": result.get("results", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to generate or send PDF report")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF report: {str(e)}"
        )

@router.post("/send-daily-summary")
async def send_daily_summary_now(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send daily summary immediately"""
    try:
        notification_service = NotificationService(db)
        
        result = notification_service.send_daily_summary(current_user.id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Daily summary sent successfully",
                "delivery_results": result.get("results", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send daily summary")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending daily summary: {str(e)}"
        )

@router.post("/send-weekly-summary")
async def send_weekly_summary_now(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send weekly summary immediately"""
    try:
        notification_service = NotificationService(db)
        
        result = notification_service.send_weekly_summary(current_user.id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Weekly summary sent successfully",
                "delivery_results": result.get("results", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send weekly summary")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending weekly summary: {str(e)}"
        )

@router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
):
    """Get scheduler service status (admin-like info for users)"""
    try:
        scheduler = get_scheduler()
        status = scheduler.get_scheduler_status()
        
        # Return user-relevant information only
        return {
            "scheduler_active": status.get("scheduler_running", False),
            "total_users": status.get("total_users", 0),
            "verified_users": status.get("verified_users", 0),
            "notifications_today": status.get("notifications_today", 0),
            "service_status": status.get("status", "unknown")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting scheduler status: {str(e)}"
        )

@router.get("/stats")
async def get_user_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notification statistics"""
    try:
        from datetime import datetime, timedelta
        from app.models.db_models import NotificationLog
        
        # Get notification counts by type for last 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        
        notifications = db.query(NotificationLog).filter(
            NotificationLog.user_id == current_user.id,
            NotificationLog.created_at >= cutoff_date
        ).all()
        
        # Group by type
        stats_by_type = {}
        total_sent = 0
        total_failed = 0
        
        for notif in notifications:
            notif_type = notif.notification_type
            if notif_type not in stats_by_type:
                stats_by_type[notif_type] = {"sent": 0, "failed": 0}
            
            if notif.status == "sent":
                stats_by_type[notif_type]["sent"] += 1
                total_sent += 1
            elif notif.status == "failed":
                stats_by_type[notif_type]["failed"] += 1
                total_failed += 1
        
        return {
            "period": "Last 30 days",
            "total_notifications": len(notifications),
            "total_sent": total_sent,
            "total_failed": total_failed,
            "success_rate": round((total_sent / len(notifications)) * 100, 1) if notifications else 0,
            "by_type": stats_by_type,
            "phone_verified": current_user.phone_verified,
            "email_available": current_user.email is not None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting notification stats: {str(e)}"
        )
