# 🚀 FITKIT Notification System

A comprehensive WhatsApp and Email notification system for the FITKIT nutrition tracking application.

## 🌟 Features

### 📱 WhatsApp Notifications
- **Meal Reminders**: Automated reminders when users haven't logged food for 5+ hours
- **Daily Summaries**: End-of-day nutrition summaries with insights
- **Weekly Reports**: Comprehensive weekly nutrition analysis
- **Monthly Reports**: Detailed monthly reports with trends and recommendations
- **PDF Delivery**: Notification when PDF reports are ready via email

### 📧 Email Notifications
- **PDF Reports**: Comprehensive nutrition reports with charts and insights
- **Daily/Weekly/Monthly Summaries**: Detailed nutrition analysis via email
- **Backup Delivery**: Email delivery when WhatsApp is unavailable

### 🔐 Phone Verification
- **OTP Verification**: 6-digit OTP sent via WhatsApp for phone verification
- **International Format**: Supports international phone numbers
- **Secure**: OTP expires in 5 minutes for security

### ⏰ Smart Scheduling
- **Quiet Hours**: Respects user-defined quiet hours (default: 10 PM - 7 AM)
- **Frequency Control**: Customizable reminder frequency (1-24 hours)
- **Background Service**: Automated scheduling with health checks

### 📊 Advanced Features
- **AI-Generated Content**: Personalized messages using Gemini AI
- **PDF Reports**: Professional reports with charts and insights
- **Notification History**: Complete log of all sent notifications
- **Preference Management**: Granular control over notification types

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Add these variables to your `.env` file:

```env
# Twilio Configuration (Required for WhatsApp)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Email Configuration (Required for Email notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@fitkit.com

# JWT Secret for OTP tokens
JWT_SECRET=your-secret-key-change-in-production

# App Configuration
APP_NAME=FITKIT
APP_URL=http://localhost:8000
```

### 3. Database Migration

Run the migration script to add notification system tables:

```bash
python migrate_notifications.py
```

Or for automatic migration:

```bash
python migrate_notifications.py --auto
```

### 4. Start the Application

```bash
uvicorn app.main:app --reload
```

The notification scheduler will start automatically with the application.

## 📱 API Endpoints

### Phone Verification

#### Send OTP
```http
POST /notifications/phone/send-otp
Content-Type: application/json

{
  "phone_number": "+919876543210"
}
```

#### Verify OTP
```http
POST /notifications/phone/verify-otp
Content-Type: application/json

{
  "otp": "123456"
}
```

#### Check Phone Status
```http
GET /notifications/phone/status
```

### Notification Preferences

#### Get Preferences
```http
GET /notifications/preferences
```

#### Update Preferences
```http
PUT /notifications/preferences
Content-Type: application/json

{
  "whatsapp_enabled": true,
  "email_enabled": true,
  "reminder_frequency": 5,
  "daily_summary": true,
  "weekly_summary": true,
  "monthly_summary": true,
  "quiet_hours_start": 22,
  "quiet_hours_end": 7
}
```

### Manual Notifications

#### Send Test Reminder
```http
POST /notifications/test-reminder
```

#### Export PDF Report
```http
POST /notifications/export-pdf
Content-Type: application/json

{
  "report_type": "weekly",
  "days_back": 7
}
```

#### Send Daily Summary
```http
POST /notifications/send-daily-summary
```

#### Send Weekly Summary
```http
POST /notifications/send-weekly-summary
```

### Notification History

#### Get History
```http
GET /notifications/history?limit=50
```

#### Get Statistics
```http
GET /notifications/stats
```

## 🔧 Configuration Options

### Notification Preferences

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `whatsapp_enabled` | boolean | `true` | Enable WhatsApp notifications |
| `email_enabled` | boolean | `true` | Enable email notifications |
| `reminder_frequency` | integer | `5` | Hours between meal reminders |
| `daily_summary` | boolean | `true` | Send daily nutrition summaries |
| `weekly_summary` | boolean | `true` | Send weekly nutrition reports |
| `monthly_summary` | boolean | `true` | Send monthly nutrition reports |
| `quiet_hours_start` | integer | `22` | Start of quiet hours (24-hour format) |
| `quiet_hours_end` | integer | `7` | End of quiet hours (24-hour format) |

### Scheduler Configuration

The scheduler runs the following tasks:

- **Meal Reminders**: Every 2 hours during active hours
- **Daily Summaries**: Daily at 9:00 PM
- **Weekly Summaries**: Sundays at 8:00 PM
- **Monthly Summaries**: 1st of month at 7:00 PM
- **Cleanup**: Daily at 2:00 AM (removes old logs and files)
- **Health Check**: Every 30 minutes

## 📊 PDF Reports

### Report Types

1. **Weekly Report** (7 days)
   - Executive summary
   - Nutrition overview
   - Meal analysis
   - Trends and recommendations

2. **Monthly Report** (30 days)
   - Comprehensive analysis
   - Charts and visualizations
   - AI-powered insights
   - Goal progress tracking

3. **Quarterly Report** (90 days)
   - Long-term trends
   - Seasonal analysis
   - Advanced recommendations

### Report Contents

- **Executive Summary**: AI-generated overview
- **Nutrition Overview**: Detailed macro/micronutrient analysis
- **Meal Analysis**: Frequency and pattern analysis
- **Trends**: Weekly/monthly progression charts
- **Recommendations**: Personalized AI suggestions
- **Goals Progress**: Achievement tracking
- **Charts**: Visual data representation

## 🔍 Monitoring & Debugging

### Health Check

Check system status:

```http
GET /health
```

Response includes scheduler status and feature availability.

### Scheduler Status

```http
GET /notifications/scheduler/status
```

### Notification Logs

All notifications are logged in the `notification_logs` table with:

- Notification type
- Delivery channel
- Status (pending/sent/failed)
- Timestamps
- Error messages (if any)
- Twilio message SID (for WhatsApp)

### Log Files

The scheduler service logs to console with structured logging:

```
INFO:scheduler_service:Meal reminders: 5 sent, 12 users checked
INFO:scheduler_service:Daily summaries completed: 8 sent to 10 eligible users
```

## 🚨 Troubleshooting

### Common Issues

#### 1. WhatsApp Messages Not Sending

**Check:**
- Twilio credentials in `.env`
- Phone number format (must include country code)
- Twilio account balance
- WhatsApp sandbox approval (for development)

**Solution:**
```bash
# Test Twilio connection
curl -X POST https://api.twilio.com/2010-04-01/Accounts/YOUR_SID/Messages.json \
  --data-urlencode "From=whatsapp:+14155238886" \
  --data-urlencode "Body=Test message" \
  --data-urlencode "To=whatsapp:+919876543210" \
  -u YOUR_SID:YOUR_AUTH_TOKEN
```

#### 2. Email Not Sending

**Check:**
- SMTP credentials in `.env`
- App password (not regular password for Gmail)
- Firewall/network restrictions

**Solution:**
```python
# Test SMTP connection
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_app_password')
```

#### 3. Scheduler Not Running

**Check:**
- Application startup logs
- Database connectivity
- Background thread status

**Solution:**
```python
from app.services.scheduler_service import get_scheduler
status = get_scheduler().get_scheduler_status()
print(status)
```

#### 4. PDF Generation Fails

**Check:**
- Matplotlib backend configuration
- File permissions for reports directory
- Available disk space

**Solution:**
```python
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Considerations

### OTP Security
- OTPs expire in 5 minutes
- 6-digit random generation
- Stored hashed in database
- Automatic cleanup of expired OTPs

### Phone Number Privacy
- Phone numbers stored encrypted
- Unique constraint prevents duplicates
- Optional field (users can opt-out)

### API Security
- All endpoints require authentication
- Rate limiting recommended for production
- Input validation on all parameters

### Data Retention
- Notification logs cleaned up after 90 days
- PDF reports deleted after 7 days
- OTPs cleaned up automatically

## 📈 Performance Optimization

### Database Indexing

Add these indexes for better performance:

```sql
CREATE INDEX idx_notification_logs_user_id ON notification_logs(user_id);
CREATE INDEX idx_notification_logs_created_at ON notification_logs(created_at);
CREATE INDEX idx_users_phone_verified ON users(phone_verified);
CREATE INDEX idx_users_last_meal_time ON users(last_meal_time);
```

### Caching

Consider implementing caching for:
- User notification preferences
- Frequently generated reports
- AI-generated content

### Background Processing

For high-volume deployments:
- Use Celery for background tasks
- Implement message queues (Redis/RabbitMQ)
- Scale scheduler horizontally

## 🤝 Contributing

### Adding New Notification Types

1. Update `NotificationService` class
2. Add new notification type to enum
3. Create message template
4. Update scheduler if needed
5. Add API endpoint if required

### Extending PDF Reports

1. Modify `PDFReportService` class
2. Add new sections to report generation
3. Update chart generation if needed
4. Test with sample data

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review application logs
3. Test individual components
4. Check Twilio/email provider status

## 🎉 Success! 

Your FITKIT application now has a comprehensive notification system that will:

- ✅ Send personalized meal reminders via WhatsApp
- ✅ Generate and deliver detailed PDF reports
- ✅ Provide daily, weekly, and monthly nutrition summaries
- ✅ Handle phone verification with OTP
- ✅ Respect user preferences and quiet hours
- ✅ Monitor and log all notification activity

Users can now stay engaged with their nutrition journey through automated, intelligent notifications delivered right to their WhatsApp and email! 🚀
