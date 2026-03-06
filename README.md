# 🍽️ Nutre-Vida - AI-Powered Nutrition Tracking & Smart Notifications

A comprehensive nutrition tracking application with AI-powered food analysis and intelligent meal recommendations.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue?style=for-the-badge&logo=sqlite)

![alt text](ScreenRecording2025-09-27224305-ezgif.com-video-to-gif-converter.gif)

## 🌟 Features

### 🤖 AI-Powered Food Analysis
- **Image Recognition**: Upload food photos for instant nutritional analysis
- **Text Analysis**: Describe your meal in text for quick logging
- **Google Gemini Integration**: Advanced AI for accurate food identification
- **Nutritional Breakdown**: Detailed calories, macros, and micronutrients
- **Portion Estimation**: Smart portion size detection and recommendations


### 📊 Comprehensive Reporting
- **Daily Summaries**: End-of-day nutrition insights
- **Weekly Reports**: Detailed analysis with trends and charts
- **Monthly Analysis**: Comprehensive health journey overview
- **PDF Generation**: Professional reports with visualizations
- **Goal Tracking**: Monitor progress towards nutrition targets

### 🎯 Intelligent Recommendations
- **Healthy Swaps**: AI-suggested healthier alternatives
- **Personalized Advice**: Tailored recommendations based on dietary preferences
- **Meal Planning**: Smart meal suggestions and planning
- **Nutritional Insights**: Deep analysis of eating patterns

### 🔐 User Management
- **Google OAuth**: Seamless authentication with Google accounts
- **Profile Management**: Customizable dietary preferences and goals
- **Privacy Controls**: Granular notification and privacy settings
- **Multi-user Support**: Individual user profiles and data isolation

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google API Key (for Gemini AI)
- Twilio Account (for WhatsApp notifications)
- Gmail Account with App Password (for email notifications)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/tharunkumarvk/celestia-main
   cd celestia-main\celestia-backend-main-functional
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```


3. **Initialize the database**
   ```bash
   python init_tables.py
   ```

4. **Start the application**
   ```bash
   cd celestia-main\celestia-backend-main-functional\celestia-fullyfunctional-backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the application**
   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`
   - Frontend: `http://localhost:3000` 

## 📱 API Endpoints

### Authentication
- `POST /users/google` - Google OAuth authentication
- `GET /users/{user_id}` - Get user profile
- `PUT /users/{user_id}` - Update user profile

### Food Analysis
- `POST /sessions/` - Create new analysis session
- `POST /analysis/upload/{session_id}` - Upload food image
- `POST /analysis/analyze/{session_id}` - Analyze uploaded image
- `POST /analysis/analyze_text/{session_id}` - Analyze text description
- `GET /analysis/results/{session_id}` - Get analysis results

### Nutrition & Recommendations
- `GET /nutrition/lookup` - Get detailed nutrition information
- `GET /recommendations/healthy-swaps` - Get healthy alternatives
- `GET /recommendations/personalized` - Get personalized recommendations

### Dashboard & Analytics
- `GET /dashboard/summary` - Get user dashboard data
- `GET /dashboard/trends` - Get nutrition trends
- `GET /dashboard/goals` - Get goal progress

## 🛠️ Configuration


## 🔄 Automated Features

### Background Scheduler
The application runs automated tasks:

- **Meal Reminders**: Every 2 hours during active hours (7 AM - 10 PM)
- **Daily Summaries**: Every day at 9:00 PM
- **Weekly Reports**: Every Sunday at 8:00 PM
- **Monthly Analysis**: 1st of each month at 7:00 PM
- **Data Cleanup**: Daily at 2:00 AM (removes old logs and temporary files)
- **Health Monitoring**: Every 30 minutes


## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] Mobile app development (React Native/Flutter)
- [ ] Advanced meal planning with grocery lists
- [ ] Integration with fitness trackers
- [ ] Social features and community challenges
- [ ] Multi-language support
- [ ] Voice-based food logging
- [ ] Barcode scanning for packaged foods
- [ ] Restaurant menu integration



**Made with ❤️ for healthier living**

*Nutre-Vida - Your AI-powered nutrition companion* 🌟
