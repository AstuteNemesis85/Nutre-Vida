import smtplib
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import jwt

from twilio.rest import Client
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.config import settings
from app.models.db_models import User, NotificationLog, Meal, DailySummary
import google.generativeai as genai

# Configure Gemini for content generation
genai.configure(api_key=settings.google_api_key)
content_model = genai.GenerativeModel("models/gemini-2.0-flash")

class NotificationService:
    """
    Comprehensive notification service for WhatsApp and Email
    Handles reminders, summaries, OTP verification, and PDF exports
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize Twilio client
        self.twilio_client = Client(
            settings.twilio_account_sid, 
            settings.twilio_auth_token
        )
        
        # Email configuration
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
    
    def send_whatsapp_message(
        self, 
        to_number: str, 
        message: str, 
        user_id: int = None,
        notification_type: str = "general"
    ) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio"""
        try:
            # Format phone number for WhatsApp
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            # Send message
            message_obj = self.twilio_client.messages.create(
                from_=settings.twilio_whatsapp_from,
                body=message,
                to=to_number
            )
            
            # Log notification
            if user_id:
                self._log_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    channel="whatsapp",
                    status="sent",
                    message_content=message,
                    twilio_sid=message_obj.sid
                )
            
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status
            }
            
        except Exception as e:
            # Log failed notification
            if user_id:
                self._log_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    channel="whatsapp",
                    status="failed",
                    message_content=message,
                    error_message=str(e)
                )
            
            print(f"WhatsApp send error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        html_body: str = None,
        attachment_path: str = None,
        user_id: int = None,
        notification_type: str = "general"
    ) -> Dict[str, Any]:
        """Send email with optional HTML body and attachment"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            # Log notification
            if user_id:
                self._log_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    channel="email",
                    status="sent",
                    message_content=f"Subject: {subject}\n\n{body}"
                )
            
            return {
                "success": True,
                "message": "Email sent successfully"
            }
            
        except Exception as e:
            # Log failed notification
            if user_id:
                self._log_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    channel="email",
                    status="failed",
                    message_content=f"Subject: {subject}\n\n{body}",
                    error_message=str(e)
                )
            
            print(f"Email send error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_phone_verification_otp(self, user_id: int, phone_number: str) -> Dict[str, Any]:
        """Send OTP for phone verification"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Generate OTP
            otp = self.generate_otp()
            
            # Store OTP in database with expiration (5 minutes)
            user.phone_otp = otp
            user.phone_otp_expires = datetime.now() + timedelta(minutes=5)
            self.db.commit()
            
            # Send OTP via WhatsApp
            message = f"""🔐 FITKIT Verification Code

Your verification code is: *{otp}*

This code will expire in 5 minutes.
Please enter this code to verify your phone number.

Stay healthy! 💪"""
            
            result = self.send_whatsapp_message(
                to_number=phone_number,
                message=message,
                user_id=user_id,
                notification_type="otp_verification"
            )
            
            return result
            
        except Exception as e:
            print(f"OTP send error: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_phone_otp(self, user_id: int, otp: str) -> Dict[str, Any]:
        """Verify OTP and mark phone as verified"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Check if OTP is valid and not expired
            if (user.phone_otp == otp and 
                user.phone_otp_expires and 
                user.phone_otp_expires > datetime.now()):
                
                # Mark phone as verified
                user.phone_verified = True
                user.phone_otp = None
                user.phone_otp_expires = None
                self.db.commit()
                
                # Send welcome message
                welcome_message = f"""✅ Phone Verified Successfully!

Welcome to FITKIT, {user.name or 'there'}! 🎉

Your phone number is now verified and you'll receive:
• Meal reminders when you haven't logged food
• Daily, weekly & monthly nutrition summaries
• PDF reports via WhatsApp & email

Let's start your healthy journey! 💪"""
                
                self.send_whatsapp_message(
                    to_number=user.phone_number,
                    message=welcome_message,
                    user_id=user_id,
                    notification_type="welcome"
                )
                
                return {"success": True, "message": "Phone verified successfully"}
            else:
                return {"success": False, "error": "Invalid or expired OTP"}
                
        except Exception as e:
            print(f"OTP verification error: {e}")
            return {"success": False, "error": str(e)}
    
    def check_and_send_meal_reminders(self) -> Dict[str, Any]:
        """Check all users and send meal reminders if needed"""
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # Get users who need reminders
            users_needing_reminders = self.db.query(User).filter(
                and_(
                    User.phone_verified == True,
                    User.phone_number.isnot(None),
                    or_(
                        User.last_meal_time.is_(None),
                        User.last_meal_time < current_time - timedelta(hours=5)
                    )
                )
            ).all()
            
            reminders_sent = 0
            
            for user in users_needing_reminders:
                # Check notification preferences
                prefs = user.notification_preferences or {}
                
                # Skip if notifications disabled
                if not prefs.get("whatsapp_enabled", True):
                    continue
                
                # Check quiet hours
                quiet_start = prefs.get("quiet_hours_start", 22)
                quiet_end = prefs.get("quiet_hours_end", 7)
                
                if quiet_start <= current_hour or current_hour < quiet_end:
                    continue  # Skip during quiet hours
                
                # Check if we already sent a reminder recently
                recent_reminder = self.db.query(NotificationLog).filter(
                    and_(
                        NotificationLog.user_id == user.id,
                        NotificationLog.notification_type == "meal_reminder",
                        NotificationLog.created_at > current_time - timedelta(hours=2)
                    )
                ).first()
                
                if recent_reminder:
                    continue  # Skip if reminder sent in last 2 hours
                
                # Generate personalized reminder message
                reminder_message = self._generate_meal_reminder_message(user)
                
                # Send reminder
                result = self.send_whatsapp_message(
                    to_number=user.phone_number,
                    message=reminder_message,
                    user_id=user.id,
                    notification_type="meal_reminder"
                )
                
                if result.get("success"):
                    reminders_sent += 1
            
            return {
                "success": True,
                "reminders_sent": reminders_sent,
                "users_checked": len(users_needing_reminders)
            }
            
        except Exception as e:
            print(f"Meal reminder check error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_meal_reminder_message(self, user: User) -> str:
        """Generate personalized meal reminder message"""
        try:
            # Get user's recent meal history for context
            recent_meals = self.db.query(Meal).filter(
                Meal.user_id == user.id
            ).order_by(Meal.upload_time.desc()).limit(3).all()
            
            # Create context for AI
            context = {
                "user_name": user.name or "there",
                "last_meal_time": user.last_meal_time.strftime("%I:%M %p") if user.last_meal_time else "unknown",
                "recent_meals": [meal.meal_type for meal in recent_meals if meal.meal_type],
                "current_time": datetime.now().strftime("%I:%M %p")
            }
            
            prompt = f"""
            Generate a friendly, encouraging WhatsApp meal reminder message for a FITKIT user.
            
            Context:
            - User name: {context['user_name']}
            - Last meal time: {context['last_meal_time']}
            - Recent meal types: {context['recent_meals']}
            - Current time: {context['current_time']}
            
            Requirements:
            - Keep it under 150 characters
            - Be warm and encouraging, not pushy
            - Include relevant emoji
            - Suggest appropriate meal for current time
            - Reference their health journey positively
            
            Make it feel personal and motivating!
            """
            
            response = content_model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"AI reminder generation error: {e}")
            # Fallback to simple reminder
            current_hour = datetime.now().hour
            if 6 <= current_hour < 11:
                meal_suggestion = "breakfast"
            elif 11 <= current_hour < 16:
                meal_suggestion = "lunch"
            elif 16 <= current_hour < 19:
                meal_suggestion = "snack"
            else:
                meal_suggestion = "dinner"
            
            return f"🍽️ Hey {user.name or 'there'}! Time for {meal_suggestion}? Don't forget to log your meal in FITKIT. Your health journey matters! 💪"
    
    def send_daily_summary(self, user_id: int) -> Dict[str, Any]:
        """Send daily nutrition summary"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Check if user wants daily summaries
            prefs = user.notification_preferences or {}
            if not prefs.get("daily_summary", True):
                return {"success": True, "message": "Daily summary disabled"}
            
            # Get today's summary
            today = datetime.now().date()
            daily_summary = self.db.query(DailySummary).filter(
                and_(
                    DailySummary.user_id == user_id,
                    DailySummary.date == today
                )
            ).first()
            
            if not daily_summary:
                return {"success": False, "error": "No data for today"}
            
            # Generate summary message
            summary_message = self._generate_daily_summary_message(user, daily_summary)
            
            results = []
            
            # Send WhatsApp if enabled
            if prefs.get("whatsapp_enabled", True) and user.phone_verified:
                whatsapp_result = self.send_whatsapp_message(
                    to_number=user.phone_number,
                    message=summary_message,
                    user_id=user_id,
                    notification_type="daily_summary"
                )
                results.append(("whatsapp", whatsapp_result))
            
            # Send Email if enabled
            if prefs.get("email_enabled", True) and user.email:
                email_result = self.send_email(
                    to_email=user.email,
                    subject=f"📊 Your Daily Nutrition Summary - {today.strftime('%B %d, %Y')}",
                    body=summary_message,
                    user_id=user_id,
                    notification_type="daily_summary"
                )
                results.append(("email", email_result))
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            print(f"Daily summary error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_daily_summary_message(self, user: User, daily_summary: DailySummary) -> str:
        """Generate daily summary message"""
        try:
            # Get user's goals
            goals = user.daily_goals or {}
            goal_calories = goals.get("calories", 2000)
            goal_protein = goals.get("protein", 60)
            
            # Calculate percentages
            calorie_percent = round((daily_summary.total_calories / goal_calories) * 100) if goal_calories > 0 else 0
            protein_percent = round((daily_summary.total_protein / goal_protein) * 100) if goal_protein > 0 else 0
            
            prompt = f"""
            Generate a daily nutrition summary message for WhatsApp/Email.
            
            User: {user.name or 'User'}
            Date: {daily_summary.date.strftime('%B %d, %Y')}
            
            Today's Stats:
            - Calories: {daily_summary.total_calories:.0f} / {goal_calories} ({calorie_percent}%)
            - Protein: {daily_summary.total_protein:.1f}g / {goal_protein}g ({protein_percent}%)
            - Carbs: {daily_summary.total_carbs:.1f}g
            - Fat: {daily_summary.total_fat:.1f}g
            - Fiber: {daily_summary.total_fiber:.1f}g
            - Meals logged: {daily_summary.meals_count}
            
            Requirements:
            - Congratulate achievements
            - Provide gentle guidance for improvements
            - Include relevant emojis
            - Keep encouraging tone
            - Suggest tomorrow's focus
            - Keep under 300 words
            """
            
            response = content_model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Daily summary generation error: {e}")
            # Fallback summary
            return f"""📊 Daily Summary - {daily_summary.date.strftime('%B %d')}

🍽️ Meals logged: {daily_summary.meals_count}
🔥 Calories: {daily_summary.total_calories:.0f}
💪 Protein: {daily_summary.total_protein:.1f}g
🌾 Carbs: {daily_summary.total_carbs:.1f}g
🥑 Fat: {daily_summary.total_fat:.1f}g

Keep up the great work! 🎉"""
    
    def send_weekly_summary(self, user_id: int) -> Dict[str, Any]:
        """Send weekly nutrition summary with insights"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Check if user wants weekly summaries
            prefs = user.notification_preferences or {}
            if not prefs.get("weekly_summary", True):
                return {"success": True, "message": "Weekly summary disabled"}
            
            # Get last 7 days of summaries
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
            
            weekly_summaries = self.db.query(DailySummary).filter(
                and_(
                    DailySummary.user_id == user_id,
                    DailySummary.date >= start_date,
                    DailySummary.date <= end_date
                )
            ).order_by(DailySummary.date).all()
            
            if not weekly_summaries:
                return {"success": False, "error": "No data for this week"}
            
            # Generate weekly summary with AI insights
            summary_message = self._generate_weekly_summary_message(user, weekly_summaries)
            
            results = []
            
            # Send via enabled channels
            if prefs.get("whatsapp_enabled", True) and user.phone_verified:
                whatsapp_result = self.send_whatsapp_message(
                    to_number=user.phone_number,
                    message=summary_message,
                    user_id=user_id,
                    notification_type="weekly_summary"
                )
                results.append(("whatsapp", whatsapp_result))
            
            if prefs.get("email_enabled", True) and user.email:
                email_result = self.send_email(
                    to_email=user.email,
                    subject=f"📈 Your Weekly Nutrition Report - Week of {start_date.strftime('%B %d')}",
                    body=summary_message,
                    user_id=user_id,
                    notification_type="weekly_summary"
                )
                results.append(("email", email_result))
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            print(f"Weekly summary error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_weekly_summary_message(self, user: User, summaries: List[DailySummary]) -> str:
        """Generate weekly summary with AI insights"""
        try:
            # Calculate weekly totals and averages
            total_calories = sum(s.total_calories for s in summaries)
            total_protein = sum(s.total_protein for s in summaries)
            total_meals = sum(s.meals_count for s in summaries)
            days_tracked = len(summaries)
            
            avg_calories = total_calories / days_tracked if days_tracked > 0 else 0
            avg_protein = total_protein / days_tracked if days_tracked > 0 else 0
            
            # Get user goals
            goals = user.daily_goals or {}
            goal_calories = goals.get("calories", 2000)
            goal_protein = goals.get("protein", 60)
            
            prompt = f"""
            Generate a comprehensive weekly nutrition summary for {user.name or 'User'}.
            
            Week Stats:
            - Days tracked: {days_tracked}/7
            - Total meals: {total_meals}
            - Average daily calories: {avg_calories:.0f} (Goal: {goal_calories})
            - Average daily protein: {avg_protein:.1f}g (Goal: {goal_protein}g)
            - Total calories this week: {total_calories:.0f}
            
            Requirements:
            - Celebrate consistency and achievements
            - Identify patterns and trends
            - Suggest specific improvements for next week
            - Include nutritional deficiency warnings if any
            - Motivational and actionable advice
            - Include emojis and keep engaging
            - Mention specific nutrients to focus on
            """
            
            response = content_model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Weekly summary generation error: {e}")
            # Fallback summary
            days_tracked = len(summaries)
            avg_calories = sum(s.total_calories for s in summaries) / days_tracked if days_tracked > 0 else 0
            
            return f"""📈 Weekly Summary

🗓️ Days tracked: {days_tracked}/7
🍽️ Total meals: {sum(s.meals_count for s in summaries)}
🔥 Avg daily calories: {avg_calories:.0f}
💪 Avg daily protein: {sum(s.total_protein for s in summaries) / days_tracked:.1f}g

Great progress this week! Keep it up! 🎉"""
    
    def send_pdf_export(self, user_id: int, pdf_path: str, report_type: str = "comprehensive") -> Dict[str, Any]:
        """Send PDF report via WhatsApp and Email"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            if not os.path.exists(pdf_path):
                return {"success": False, "error": "PDF file not found"}
            
            prefs = user.notification_preferences or {}
            results = []
            
            # Prepare message
            message = f"""📄 Your FITKIT {report_type.title()} Report

Hi {user.name or 'there'}! 👋

Your personalized nutrition report is ready! This comprehensive analysis includes:

✅ Detailed nutrition breakdown
✅ Health insights & recommendations  
✅ Progress tracking & trends
✅ Personalized improvement suggestions

Keep up the amazing work on your health journey! 💪

Best regards,
FITKIT Team 🌟"""
            
            # Send via WhatsApp (Twilio doesn't support file attachments, so we send a message)
            if prefs.get("whatsapp_enabled", True) and user.phone_verified:
                whatsapp_message = f"""{message}

📧 Check your email for the detailed PDF report!"""
                
                whatsapp_result = self.send_whatsapp_message(
                    to_number=user.phone_number,
                    message=whatsapp_message,
                    user_id=user_id,
                    notification_type="pdf_export"
                )
                results.append(("whatsapp", whatsapp_result))
            
            # Send via Email with PDF attachment
            if prefs.get("email_enabled", True) and user.email:
                email_subject = f"📊 Your FITKIT {report_type.title()} Report - {datetime.now().strftime('%B %d, %Y')}"
                
                email_result = self.send_email(
                    to_email=user.email,
                    subject=email_subject,
                    body=message,
                    attachment_path=pdf_path,
                    user_id=user_id,
                    notification_type="pdf_export"
                )
                results.append(("email", email_result))
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            print(f"PDF export error: {e}")
            return {"success": False, "error": str(e)}
    
    def _log_notification(
        self, 
        user_id: int, 
        notification_type: str, 
        channel: str, 
        status: str,
        message_content: str = None,
        twilio_sid: str = None,
        error_message: str = None
    ):
        """Log notification to database"""
        try:
            notification_log = NotificationLog(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                status=status,
                message_content=message_content,
                twilio_sid=twilio_sid,
                error_message=error_message,
                sent_at=datetime.now() if status == "sent" else None
            )
            
            self.db.add(notification_log)
            self.db.commit()
            
        except Exception as e:
            print(f"Notification logging error: {e}")
            self.db.rollback()
    
    def get_notification_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's notification history"""
        try:
            notifications = self.db.query(NotificationLog).filter(
                NotificationLog.user_id == user_id
            ).order_by(NotificationLog.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": notif.id,
                    "type": notif.notification_type,
                    "channel": notif.channel,
                    "status": notif.status,
                    "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                    "created_at": notif.created_at.isoformat(),
                    "error": notif.error_message
                }
                for notif in notifications
            ]
            
        except Exception as e:
            print(f"Notification history error: {e}")
            return []
    
    def update_notification_preferences(self, user_id: int, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's notification preferences"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Update preferences
            current_prefs = user.notification_preferences or {}
            current_prefs.update(preferences)
            user.notification_preferences = current_prefs
            
            self.db.commit()
            
            return {
                "success": True,
                "preferences": current_prefs
            }
            
        except Exception as e:
            print(f"Preferences update error: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
