import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from threading import Thread
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import SessionLocal
from app.models.db_models import User, NotificationLog
from app.services.notification_service import NotificationService
from app.services.pdf_report_service import PDFReportService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Background scheduler service for automated notifications and reports
    Handles meal reminders, daily/weekly/monthly summaries, and cleanup tasks
    """
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        
    def start(self):
        """Start the scheduler service"""
        if self.running:
            logger.info("Scheduler already running")
            return
        
        self.running = True
        
        # Schedule tasks
        self._schedule_tasks()
        
        # Start scheduler in background thread
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler service started")
    
    def stop(self):
        """Stop the scheduler service"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Scheduler service stopped")
    
    def _schedule_tasks(self):
        """Schedule all recurring tasks"""
        
        # Meal reminders - every 2 hours during active hours
        schedule.every(2).hours.do(self._check_meal_reminders)
        
        # Daily summaries - at 9 PM every day
        schedule.every().day.at("21:00").do(self._send_daily_summaries)
        
        # Weekly summaries - every Sunday at 8 PM
        schedule.every().sunday.at("20:00").do(self._send_weekly_summaries)
        
        # Monthly summaries - first day of month at 7 PM
        schedule.every().day.at("19:00").do(self._check_monthly_summaries)
        
        # Cleanup old notifications - daily at 2 AM
        schedule.every().day.at("02:00").do(self._cleanup_old_data)
        
        # Health check - every 30 minutes
        schedule.every(30).minutes.do(self._health_check)
        
        logger.info("Scheduled tasks configured")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _check_meal_reminders(self):
        """Check and send meal reminders"""
        try:
            logger.info("Checking meal reminders...")
            
            db = SessionLocal()
            notification_service = NotificationService(db)
            
            result = notification_service.check_and_send_meal_reminders()
            
            if result.get("success"):
                reminders_sent = result.get("reminders_sent", 0)
                users_checked = result.get("users_checked", 0)
                logger.info(f"Meal reminders: {reminders_sent} sent, {users_checked} users checked")
            else:
                logger.error(f"Meal reminder check failed: {result.get('error')}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error checking meal reminders: {e}")
    
    def _send_daily_summaries(self):
        """Send daily summaries to all eligible users"""
        try:
            logger.info("Sending daily summaries...")
            
            db = SessionLocal()
            notification_service = NotificationService(db)
            
            # Get users who want daily summaries
            users = db.query(User).filter(
                and_(
                    User.phone_verified == True,
                    User.notification_preferences.op('->>')('daily_summary').astext == 'true'
                )
            ).all()
            
            summaries_sent = 0
            
            for user in users:
                try:
                    result = notification_service.send_daily_summary(user.id)
                    if result.get("success"):
                        summaries_sent += 1
                        logger.info(f"Daily summary sent to user {user.id}")
                    else:
                        logger.warning(f"Failed to send daily summary to user {user.id}: {result.get('error')}")
                except Exception as e:
                    logger.error(f"Error sending daily summary to user {user.id}: {e}")
            
            logger.info(f"Daily summaries completed: {summaries_sent} sent to {len(users)} eligible users")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error sending daily summaries: {e}")
    
    def _send_weekly_summaries(self):
        """Send weekly summaries to all eligible users"""
        try:
            logger.info("Sending weekly summaries...")
            
            db = SessionLocal()
            notification_service = NotificationService(db)
            
            # Get users who want weekly summaries
            users = db.query(User).filter(
                and_(
                    User.phone_verified == True,
                    User.notification_preferences.op('->>')('weekly_summary').astext == 'true'
                )
            ).all()
            
            summaries_sent = 0
            
            for user in users:
                try:
                    result = notification_service.send_weekly_summary(user.id)
                    if result.get("success"):
                        summaries_sent += 1
                        logger.info(f"Weekly summary sent to user {user.id}")
                    else:
                        logger.warning(f"Failed to send weekly summary to user {user.id}: {result.get('error')}")
                except Exception as e:
                    logger.error(f"Error sending weekly summary to user {user.id}: {e}")
            
            logger.info(f"Weekly summaries completed: {summaries_sent} sent to {len(users)} eligible users")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error sending weekly summaries: {e}")
    
    def _check_monthly_summaries(self):
        """Check if it's the first day of month and send monthly summaries"""
        try:
            # Only run on first day of month
            if datetime.now().day != 1:
                return
            
            logger.info("Sending monthly summaries...")
            
            db = SessionLocal()
            notification_service = NotificationService(db)
            pdf_service = PDFReportService(db)
            
            # Get users who want monthly summaries
            users = db.query(User).filter(
                and_(
                    User.phone_verified == True,
                    User.notification_preferences.op('->>')('monthly_summary').astext == 'true'
                )
            ).all()
            
            summaries_sent = 0
            
            for user in users:
                try:
                    # Generate monthly PDF report
                    pdf_path = pdf_service.generate_comprehensive_report(
                        user_id=user.id,
                        report_type="monthly",
                        days_back=30
                    )
                    
                    # Send PDF via notifications
                    result = notification_service.send_pdf_export(
                        user_id=user.id,
                        pdf_path=pdf_path,
                        report_type="monthly"
                    )
                    
                    if result.get("success"):
                        summaries_sent += 1
                        logger.info(f"Monthly summary sent to user {user.id}")
                    else:
                        logger.warning(f"Failed to send monthly summary to user {user.id}: {result.get('error')}")
                    
                    # Clean up PDF file
                    import os
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                        
                except Exception as e:
                    logger.error(f"Error sending monthly summary to user {user.id}: {e}")
            
            logger.info(f"Monthly summaries completed: {summaries_sent} sent to {len(users)} eligible users")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error sending monthly summaries: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old notification logs and temporary files"""
        try:
            logger.info("Running cleanup tasks...")
            
            db = SessionLocal()
            
            # Clean up old notification logs (older than 90 days)
            cutoff_date = datetime.now() - timedelta(days=90)
            
            old_notifications = db.query(NotificationLog).filter(
                NotificationLog.created_at < cutoff_date
            ).count()
            
            if old_notifications > 0:
                db.query(NotificationLog).filter(
                    NotificationLog.created_at < cutoff_date
                ).delete()
                
                db.commit()
                logger.info(f"Cleaned up {old_notifications} old notification logs")
            
            # Clean up old report files
            import os
            import glob
            
            reports_dir = "reports"
            if os.path.exists(reports_dir):
                # Remove files older than 7 days
                cutoff_timestamp = time.time() - (7 * 24 * 60 * 60)
                
                for file_path in glob.glob(os.path.join(reports_dir, "*")):
                    try:
                        if os.path.getmtime(file_path) < cutoff_timestamp:
                            os.remove(file_path)
                            logger.info(f"Cleaned up old report file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up file {file_path}: {e}")
            
            # Clean up expired OTPs
            expired_otp_users = db.query(User).filter(
                and_(
                    User.phone_otp.isnot(None),
                    User.phone_otp_expires < datetime.now()
                )
            ).all()
            
            for user in expired_otp_users:
                user.phone_otp = None
                user.phone_otp_expires = None
            
            if expired_otp_users:
                db.commit()
                logger.info(f"Cleaned up {len(expired_otp_users)} expired OTPs")
            
            db.close()
            
            logger.info("Cleanup tasks completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _health_check(self):
        """Perform health check and log system status"""
        try:
            db = SessionLocal()
            
            # Check database connectivity
            user_count = db.query(User).count()
            
            # Check recent notification activity
            recent_notifications = db.query(NotificationLog).filter(
                NotificationLog.created_at > datetime.now() - timedelta(hours=24)
            ).count()
            
            logger.info(f"Health check: {user_count} users, {recent_notifications} notifications in last 24h")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def send_immediate_reminder(self, user_id: int) -> Dict[str, Any]:
        """Send immediate meal reminder to specific user"""
        try:
            db = SessionLocal()
            notification_service = NotificationService(db)
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            if not user.phone_verified or not user.phone_number:
                return {"success": False, "error": "User phone not verified"}
            
            # Generate and send reminder
            reminder_message = notification_service._generate_meal_reminder_message(user)
            
            result = notification_service.send_whatsapp_message(
                to_number=user.phone_number,
                message=reminder_message,
                user_id=user_id,
                notification_type="manual_reminder"
            )
            
            db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending immediate reminder to user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_and_send_report(self, user_id: int, report_type: str = "weekly") -> Dict[str, Any]:
        """Generate and send report immediately"""
        try:
            db = SessionLocal()
            notification_service = NotificationService(db)
            pdf_service = PDFReportService(db)
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Determine days back based on report type
            days_back = {
                "weekly": 7,
                "monthly": 30,
                "quarterly": 90
            }.get(report_type, 7)
            
            # Generate PDF report
            pdf_path = pdf_service.generate_comprehensive_report(
                user_id=user_id,
                report_type=report_type,
                days_back=days_back
            )
            
            # Send report
            result = notification_service.send_pdf_export(
                user_id=user_id,
                pdf_path=pdf_path,
                report_type=report_type
            )
            
            # Clean up PDF file after sending
            import os
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating report for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and statistics"""
        try:
            db = SessionLocal()
            
            # Get notification statistics
            today = datetime.now().date()
            
            today_notifications = db.query(NotificationLog).filter(
                NotificationLog.created_at >= today
            ).count()
            
            week_notifications = db.query(NotificationLog).filter(
                NotificationLog.created_at >= today - timedelta(days=7)
            ).count()
            
            # Get user statistics
            total_users = db.query(User).count()
            verified_users = db.query(User).filter(User.phone_verified == True).count()
            
            # Get recent notification types
            recent_types = db.query(NotificationLog.notification_type).filter(
                NotificationLog.created_at >= today - timedelta(days=1)
            ).distinct().all()
            
            db.close()
            
            return {
                "scheduler_running": self.running,
                "total_users": total_users,
                "verified_users": verified_users,
                "notifications_today": today_notifications,
                "notifications_this_week": week_notifications,
                "recent_notification_types": [t[0] for t in recent_types],
                "next_scheduled_tasks": [
                    str(job) for job in schedule.jobs[:5]  # Next 5 jobs
                ],
                "status": "healthy" if self.running else "stopped"
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                "scheduler_running": self.running,
                "status": "error",
                "error": str(e)
            }

# Global scheduler instance
scheduler_service = SchedulerService()

def start_scheduler():
    """Start the global scheduler service"""
    scheduler_service.start()

def stop_scheduler():
    """Stop the global scheduler service"""
    scheduler_service.stop()

def get_scheduler() -> SchedulerService:
    """Get the global scheduler instance"""
    return scheduler_service
