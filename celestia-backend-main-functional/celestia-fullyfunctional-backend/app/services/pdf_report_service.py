import os
import io
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.db_models import User, Meal, DailySummary
from app.config import settings
import google.generativeai as genai

# Configure Gemini for insights generation
genai.configure(api_key=settings.google_api_key)
insights_model = genai.GenerativeModel("models/gemini-2.0-flash")

class PDFReportService:
    """
    Comprehensive PDF report generation service
    Creates detailed nutrition reports with charts, insights, and recommendations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # Set up matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB')
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#A23B72')
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor('#F18F01')
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        self.highlight_style = ParagraphStyle(
            'Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.HexColor('#C73E1D'),
            fontName='Helvetica-Bold'
        )
    
    def generate_comprehensive_report(
        self, 
        user_id: int, 
        report_type: str = "monthly",
        days_back: int = 30
    ) -> str:
        """Generate comprehensive nutrition report"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Create reports directory if it doesn't exist
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"FITKIT_{report_type}_report_{user.name or user_id}_{timestamp}.pdf"
            filepath = os.path.join(reports_dir, filename)
            
            # Get data for the report
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            meals_data = self._get_meals_data(user_id, start_date, end_date)
            summaries_data = self._get_summaries_data(user_id, start_date, end_date)
            
            # Generate AI insights
            ai_insights = self._generate_ai_insights(user, meals_data, summaries_data, report_type)
            
            # Create PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            
            # Add content sections
            story.extend(self._create_title_section(user, report_type, start_date, end_date))
            story.extend(self._create_executive_summary(user, summaries_data, ai_insights))
            story.extend(self._create_nutrition_overview(summaries_data, user))
            story.extend(self._create_meal_analysis(meals_data))
            story.extend(self._create_trends_section(summaries_data))
            story.extend(self._create_recommendations_section(ai_insights))
            story.extend(self._create_goals_progress(user, summaries_data))
            
            # Add charts
            charts_paths = self._generate_charts(summaries_data, user_id, timestamp)
            story.extend(self._add_charts_to_story(charts_paths))
            
            # Build PDF
            doc.build(story)
            
            # Clean up temporary chart files
            self._cleanup_temp_files(charts_paths)
            
            return filepath
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            raise e
    
    def _get_meals_data(self, user_id: int, start_date: date, end_date: date) -> List[Meal]:
        """Get meals data for the specified period"""
        return self.db.query(Meal).filter(
            and_(
                Meal.user_id == user_id,
                Meal.upload_date >= start_date,
                Meal.upload_date <= end_date
            )
        ).order_by(Meal.upload_date.desc()).all()
    
    def _get_summaries_data(self, user_id: int, start_date: date, end_date: date) -> List[DailySummary]:
        """Get daily summaries for the specified period"""
        return self.db.query(DailySummary).filter(
            and_(
                DailySummary.user_id == user_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date
            )
        ).order_by(DailySummary.date).all()
    
    def _generate_ai_insights(
        self, 
        user: User, 
        meals_data: List[Meal], 
        summaries_data: List[DailySummary],
        report_type: str
    ) -> Dict[str, Any]:
        """Generate AI-powered insights for the report"""
        try:
            # Prepare data summary for AI
            total_meals = len(meals_data)
            days_tracked = len(summaries_data)
            
            if summaries_data:
                avg_calories = sum(s.total_calories for s in summaries_data) / len(summaries_data)
                avg_protein = sum(s.total_protein for s in summaries_data) / len(summaries_data)
                avg_carbs = sum(s.total_carbs for s in summaries_data) / len(summaries_data)
                avg_fat = sum(s.total_fat for s in summaries_data) / len(summaries_data)
            else:
                avg_calories = avg_protein = avg_carbs = avg_fat = 0
            
            # Get user goals
            goals = user.daily_goals or {}
            
            # Most frequent meal types
            meal_types = [meal.meal_type for meal in meals_data if meal.meal_type]
            meal_type_counts = {}
            for meal_type in meal_types:
                meal_type_counts[meal_type] = meal_type_counts.get(meal_type, 0) + 1
            
            prompt = f"""
            Generate comprehensive nutrition insights for a {report_type} FITKIT report.
            
            User Profile:
            - Name: {user.name or 'User'}
            - Goals: {goals}
            - Preferences: {user.profile}
            
            Period Summary:
            - Days tracked: {days_tracked}
            - Total meals logged: {total_meals}
            - Average daily calories: {avg_calories:.0f}
            - Average daily protein: {avg_protein:.1f}g
            - Average daily carbs: {avg_carbs:.1f}g
            - Average daily fat: {avg_fat:.1f}g
            - Most frequent meal types: {meal_type_counts}
            
            Generate insights in JSON format with these sections:
            {{
                "executive_summary": "2-3 sentence overview of their nutrition journey",
                "key_achievements": ["achievement 1", "achievement 2", "achievement 3"],
                "areas_for_improvement": ["improvement 1", "improvement 2", "improvement 3"],
                "nutritional_deficiencies": ["deficiency 1", "deficiency 2"] or [],
                "personalized_recommendations": [
                    {{"title": "Recommendation 1", "description": "Detailed advice", "priority": "high/medium/low"}},
                    {{"title": "Recommendation 2", "description": "Detailed advice", "priority": "high/medium/low"}}
                ],
                "meal_pattern_insights": "Analysis of their eating patterns",
                "goal_progress_analysis": "How they're progressing toward their goals",
                "next_month_focus": "What to focus on next month"
            }}
            
            Make it personal, actionable, and encouraging. Focus on Indian nutrition context.
            """
            
            response = insights_model.generate_content(prompt)
            
            # Parse JSON response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._get_fallback_insights(user, summaries_data)
                
        except Exception as e:
            print(f"AI insights generation error: {e}")
            return self._get_fallback_insights(user, summaries_data)
    
    def _get_fallback_insights(self, user: User, summaries_data: List[DailySummary]) -> Dict[str, Any]:
        """Fallback insights when AI generation fails"""
        days_tracked = len(summaries_data)
        avg_calories = sum(s.total_calories for s in summaries_data) / len(summaries_data) if summaries_data else 0
        
        return {
            "executive_summary": f"You've tracked {days_tracked} days with an average of {avg_calories:.0f} calories per day. Great consistency in your health journey!",
            "key_achievements": [
                f"Tracked nutrition for {days_tracked} days",
                "Maintained consistent meal logging",
                "Building healthy habits"
            ],
            "areas_for_improvement": [
                "Increase vegetable intake",
                "Focus on protein balance",
                "Stay hydrated"
            ],
            "nutritional_deficiencies": [],
            "personalized_recommendations": [
                {"title": "Increase Fiber", "description": "Add more vegetables and whole grains", "priority": "medium"},
                {"title": "Protein Balance", "description": "Include protein in every meal", "priority": "high"}
            ],
            "meal_pattern_insights": "Your meal timing shows good consistency.",
            "goal_progress_analysis": "You're making steady progress toward your health goals.",
            "next_month_focus": "Focus on increasing vegetable intake and maintaining consistency."
        }
    
    def _create_title_section(self, user: User, report_type: str, start_date: date, end_date: date) -> List:
        """Create title section of the report"""
        story = []
        
        # Title
        title = f"FITKIT {report_type.title()} Nutrition Report"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # User info and date range
        user_info = f"""
        <b>User:</b> {user.name or 'User'}<br/>
        <b>Report Period:</b> {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}<br/>
        <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        """
        story.append(Paragraph(user_info, self.body_style))
        story.append(Spacer(1, 30))
        
        return story
    
    def _create_executive_summary(self, user: User, summaries_data: List[DailySummary], ai_insights: Dict[str, Any]) -> List:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.heading_style))
        story.append(Paragraph(ai_insights.get("executive_summary", ""), self.body_style))
        story.append(Spacer(1, 20))
        
        # Key metrics table
        if summaries_data:
            total_days = len(summaries_data)
            total_meals = sum(s.meals_count for s in summaries_data)
            avg_calories = sum(s.total_calories for s in summaries_data) / total_days
            avg_protein = sum(s.total_protein for s in summaries_data) / total_days
            
            metrics_data = [
                ['Metric', 'Value'],
                ['Days Tracked', str(total_days)],
                ['Total Meals Logged', str(total_meals)],
                ['Average Daily Calories', f"{avg_calories:.0f}"],
                ['Average Daily Protein', f"{avg_protein:.1f}g"],
                ['Tracking Consistency', f"{(total_days/30)*100:.0f}%"]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_nutrition_overview(self, summaries_data: List[DailySummary], user: User) -> List:
        """Create nutrition overview section"""
        story = []
        
        story.append(Paragraph("Nutrition Overview", self.heading_style))
        
        if not summaries_data:
            story.append(Paragraph("No nutrition data available for this period.", self.body_style))
            return story
        
        # Calculate averages
        total_days = len(summaries_data)
        avg_calories = sum(s.total_calories for s in summaries_data) / total_days
        avg_protein = sum(s.total_protein for s in summaries_data) / total_days
        avg_carbs = sum(s.total_carbs for s in summaries_data) / total_days
        avg_fat = sum(s.total_fat for s in summaries_data) / total_days
        avg_fiber = sum(s.total_fiber for s in summaries_data) / total_days
        
        # Get user goals
        goals = user.daily_goals or {}
        goal_calories = goals.get("calories", 2000)
        goal_protein = goals.get("protein", 60)
        
        # Create nutrition table
        nutrition_data = [
            ['Nutrient', 'Average Daily', 'Goal', 'Progress'],
            ['Calories', f"{avg_calories:.0f}", f"{goal_calories}", f"{(avg_calories/goal_calories)*100:.0f}%"],
            ['Protein', f"{avg_protein:.1f}g", f"{goal_protein}g", f"{(avg_protein/goal_protein)*100:.0f}%"],
            ['Carbohydrates', f"{avg_carbs:.1f}g", "250g", f"{(avg_carbs/250)*100:.0f}%"],
            ['Fat', f"{avg_fat:.1f}g", "65g", f"{(avg_fat/65)*100:.0f}%"],
            ['Fiber', f"{avg_fiber:.1f}g", "25g", f"{(avg_fiber/25)*100:.0f}%"]
        ]
        
        nutrition_table = Table(nutrition_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch])
        nutrition_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#A23B72')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(nutrition_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_meal_analysis(self, meals_data: List[Meal]) -> List:
        """Create meal analysis section"""
        story = []
        
        story.append(Paragraph("Meal Analysis", self.heading_style))
        
        if not meals_data:
            story.append(Paragraph("No meal data available for this period.", self.body_style))
            return story
        
        # Analyze meal types
        meal_types = {}
        total_meals = len(meals_data)
        
        for meal in meals_data:
            meal_type = meal.meal_type or "Unknown"
            meal_types[meal_type] = meal_types.get(meal_type, 0) + 1
        
        # Create meal distribution table
        meal_data = [['Meal Type', 'Count', 'Percentage']]
        for meal_type, count in sorted(meal_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_meals) * 100
            meal_data.append([meal_type.title(), str(count), f"{percentage:.1f}%"])
        
        meal_table = Table(meal_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        meal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F18F01')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(meal_table)
        story.append(Spacer(1, 20))
        
        # Most frequent foods
        story.append(Paragraph("Most Frequently Logged Foods", self.subheading_style))
        
        food_counts = {}
        for meal in meals_data:
            if meal.analysis_data and meal.analysis_data.get('items'):
                for item in meal.analysis_data['items']:
                    food_name = item.get('name', '').lower()
                    if food_name:
                        food_counts[food_name] = food_counts.get(food_name, 0) + 1
        
        # Top 10 foods
        top_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_foods:
            foods_text = "<br/>".join([f"• {food.title()}: {count} times" for food, count in top_foods])
            story.append(Paragraph(foods_text, self.body_style))
        else:
            story.append(Paragraph("No detailed food data available.", self.body_style))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_trends_section(self, summaries_data: List[DailySummary]) -> List:
        """Create trends analysis section"""
        story = []
        
        story.append(Paragraph("Nutrition Trends", self.heading_style))
        
        if len(summaries_data) < 7:
            story.append(Paragraph("Insufficient data for trend analysis. Need at least 7 days of data.", self.body_style))
            return story
        
        # Calculate weekly averages for trend analysis
        weekly_data = []
        current_week = []
        
        for summary in summaries_data:
            current_week.append(summary)
            if len(current_week) == 7:
                week_avg_calories = sum(s.total_calories for s in current_week) / 7
                week_avg_protein = sum(s.total_protein for s in current_week) / 7
                weekly_data.append({
                    'week': len(weekly_data) + 1,
                    'calories': week_avg_calories,
                    'protein': week_avg_protein
                })
                current_week = []
        
        if len(weekly_data) >= 2:
            # Calculate trends
            calorie_trend = weekly_data[-1]['calories'] - weekly_data[0]['calories']
            protein_trend = weekly_data[-1]['protein'] - weekly_data[0]['protein']
            
            trend_text = f"""
            <b>Calorie Trend:</b> {'+' if calorie_trend > 0 else ''}{calorie_trend:.0f} calories per day<br/>
            <b>Protein Trend:</b> {'+' if protein_trend > 0 else ''}{protein_trend:.1f}g per day<br/>
            """
            
            if calorie_trend > 100:
                trend_text += "<br/><b>Note:</b> Calorie intake has increased significantly. Consider portion control if weight management is a goal."
            elif calorie_trend < -100:
                trend_text += "<br/><b>Note:</b> Calorie intake has decreased significantly. Ensure you're meeting your energy needs."
            
            story.append(Paragraph(trend_text, self.body_style))
        else:
            story.append(Paragraph("Insufficient data for weekly trend analysis.", self.body_style))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_recommendations_section(self, ai_insights: Dict[str, Any]) -> List:
        """Create recommendations section"""
        story = []
        
        story.append(Paragraph("Personalized Recommendations", self.heading_style))
        
        # Key achievements
        achievements = ai_insights.get("key_achievements", [])
        if achievements:
            story.append(Paragraph("🎉 Key Achievements", self.subheading_style))
            for achievement in achievements:
                story.append(Paragraph(f"• {achievement}", self.body_style))
            story.append(Spacer(1, 10))
        
        # Areas for improvement
        improvements = ai_insights.get("areas_for_improvement", [])
        if improvements:
            story.append(Paragraph("🎯 Areas for Improvement", self.subheading_style))
            for improvement in improvements:
                story.append(Paragraph(f"• {improvement}", self.body_style))
            story.append(Spacer(1, 10))
        
        # Nutritional deficiencies
        deficiencies = ai_insights.get("nutritional_deficiencies", [])
        if deficiencies:
            story.append(Paragraph("⚠️ Nutritional Deficiencies", self.subheading_style))
            for deficiency in deficiencies:
                story.append(Paragraph(f"• {deficiency}", self.highlight_style))
            story.append(Spacer(1, 10))
        
        # Detailed recommendations
        recommendations = ai_insights.get("personalized_recommendations", [])
        if recommendations:
            story.append(Paragraph("💡 Detailed Recommendations", self.subheading_style))
            
            for rec in recommendations:
                priority_color = {
                    'high': colors.red,
                    'medium': colors.orange,
                    'low': colors.green
                }.get(rec.get('priority', 'medium'), colors.orange)
                
                rec_style = ParagraphStyle(
                    'RecommendationStyle',
                    parent=self.body_style,
                    leftIndent=20,
                    bulletIndent=10,
                    textColor=priority_color
                )
                
                story.append(Paragraph(f"<b>{rec.get('title', '')}</b> ({rec.get('priority', 'medium')} priority)", rec_style))
                story.append(Paragraph(rec.get('description', ''), self.body_style))
                story.append(Spacer(1, 8))
        
        # Next month focus
        next_focus = ai_insights.get("next_month_focus", "")
        if next_focus:
            story.append(Paragraph("🚀 Next Month Focus", self.subheading_style))
            story.append(Paragraph(next_focus, self.body_style))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_goals_progress(self, user: User, summaries_data: List[DailySummary]) -> List:
        """Create goals progress section"""
        story = []
        
        story.append(Paragraph("Goals Progress", self.heading_style))
        
        goals = user.daily_goals or {}
        if not goals:
            story.append(Paragraph("No specific goals set. Consider setting daily calorie and protein targets for better tracking.", self.body_style))
            return story
        
        if not summaries_data:
            story.append(Paragraph("No data available for goals analysis.", self.body_style))
            return story
        
        # Calculate goal achievement rates
        goal_calories = goals.get("calories", 2000)
        goal_protein = goals.get("protein", 60)
        
        calorie_achievements = sum(1 for s in summaries_data if s.goal_calories_achieved)
        protein_achievements = sum(1 for s in summaries_data if s.goal_protein_achieved)
        total_days = len(summaries_data)
        
        calorie_rate = (calorie_achievements / total_days) * 100
        protein_rate = (protein_achievements / total_days) * 100
        
        progress_text = f"""
        <b>Calorie Goal Achievement:</b> {calorie_achievements}/{total_days} days ({calorie_rate:.0f}%)<br/>
        <b>Protein Goal Achievement:</b> {protein_achievements}/{total_days} days ({protein_rate:.0f}%)<br/>
        """
        
        story.append(Paragraph(progress_text, self.body_style))
        
        # Progress assessment
        if calorie_rate >= 80:
            story.append(Paragraph("🎉 Excellent calorie goal consistency!", self.body_style))
        elif calorie_rate >= 60:
            story.append(Paragraph("👍 Good calorie goal progress. Keep it up!", self.body_style))
        else:
            story.append(Paragraph("📈 Room for improvement in calorie goal achievement.", self.body_style))
        
        if protein_rate >= 80:
            story.append(Paragraph("💪 Outstanding protein goal consistency!", self.body_style))
        elif protein_rate >= 60:
            story.append(Paragraph("👌 Solid protein goal progress!", self.body_style))
        else:
            story.append(Paragraph("🥩 Focus on increasing protein intake to meet your goals.", self.body_style))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _generate_charts(self, summaries_data: List[DailySummary], user_id: int, timestamp: str) -> List[str]:
        """Generate charts for the report"""
        chart_paths = []
        
        if not summaries_data:
            return chart_paths
        
        try:
            # Prepare data
            dates = [s.date for s in summaries_data]
            calories = [s.total_calories for s in summaries_data]
            proteins = [s.total_protein for s in summaries_data]
            carbs = [s.total_carbs for s in summaries_data]
            fats = [s.total_fat for s in summaries_data]
            
            # Chart 1: Daily Calories Trend
            plt.figure(figsize=(10, 6))
            plt.plot(dates, calories, marker='o', linewidth=2, markersize=6)
            plt.title('Daily Calories Trend', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Calories', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart1_path = f"reports/calories_trend_{user_id}_{timestamp}.png"
            plt.savefig(chart1_path, dpi=300, bbox_inches='tight')
            plt.close()
            chart_paths.append(chart1_path)
            
            # Chart 2: Macronutrient Distribution
            if len(summaries_data) > 0:
                avg_protein = sum(proteins) / len(proteins)
                avg_carbs = sum(carbs) / len(carbs)
                avg_fat = sum(fats) / len(fats)
                
                # Convert to calories for proper pie chart
                protein_calories = avg_protein * 4
                carbs_calories = avg_carbs * 4
                fat_calories = avg_fat * 9
                
                labels = ['Protein', 'Carbohydrates', 'Fat']
                sizes = [protein_calories, carbs_calories, fat_calories]
                colors_pie = ['#FF6B6B', '#4ECDC4', '#45B7D1']
                
                plt.figure(figsize=(8, 8))
                plt.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
                plt.title('Average Macronutrient Distribution', fontsize=16, fontweight='bold')
                plt.axis('equal')
                
                chart2_path = f"reports/macros_pie_{user_id}_{timestamp}.png"
                plt.savefig(chart2_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart2_path)
            
            # Chart 3: Weekly Progress (if enough data)
            if len(summaries_data) >= 14:
                # Group by weeks
                weekly_calories = []
                weekly_proteins = []
                week_labels = []
                
                for i in range(0, len(summaries_data), 7):
                    week_data = summaries_data[i:i+7]
                    if len(week_data) >= 5:  # At least 5 days in week
                        avg_cal = sum(s.total_calories for s in week_data) / len(week_data)
                        avg_prot = sum(s.total_protein for s in week_data) / len(week_data)
                        weekly_calories.append(avg_cal)
                        weekly_proteins.append(avg_prot)
                        week_labels.append(f"Week {len(week_labels) + 1}")
                
                if len(weekly_calories) >= 2:
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
                    
                    # Weekly calories
                    ax1.bar(week_labels, weekly_calories, color='#FF6B6B', alpha=0.7)
                    ax1.set_title('Weekly Average Calories', fontweight='bold')
                    ax1.set_ylabel('Calories')
                    ax1.grid(True, alpha=0.3)
                    
                    # Weekly protein
                    ax2.bar(week_labels, weekly_proteins, color='#4ECDC4', alpha=0.7)
                    ax2.set_title('Weekly Average Protein', fontweight='bold')
                    ax2.set_ylabel('Protein (g)')
                    ax2.set_xlabel('Week')
                    ax2.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    
                    chart3_path = f"reports/weekly_progress_{user_id}_{timestamp}.png"
                    plt.savefig(chart3_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    chart_paths.append(chart3_path)
            
        except Exception as e:
            print(f"Chart generation error: {e}")
        
        return chart_paths
    
    def _add_charts_to_story(self, chart_paths: List[str]) -> List:
        """Add charts to the PDF story"""
        story = []
        
        if not chart_paths:
            return story
        
        story.append(PageBreak())
        story.append(Paragraph("Nutrition Charts & Trends", self.heading_style))
        story.append(Spacer(1, 20))
        
        for chart_path in chart_paths:
            if os.path.exists(chart_path):
                try:
                    # Add chart image
                    img = Image(chart_path, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 20))
                except Exception as e:
                    print(f"Error adding chart {chart_path}: {e}")
        
        return story
    
    def _cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")
    
    def generate_quick_summary_pdf(self, user_id: int, days_back: int = 7) -> str:
        """Generate a quick summary PDF for recent days"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Create reports directory
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"FITKIT_quick_summary_{user.name or user_id}_{timestamp}.pdf"
            filepath = os.path.join(reports_dir, filename)
            
            # Get recent data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            summaries_data = self._get_summaries_data(user_id, start_date, end_date)
            
            # Create simple PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            
            # Title
            story.append(Paragraph(f"FITKIT Quick Summary - Last {days_back} Days", self.title_style))
            story.append(Spacer(1, 20))
            
            # User info
            user_info = f"<b>User:</b> {user.name or 'User'}<br/><b>Period:</b> {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
            story.append(Paragraph(user_info, self.body_style))
            story.append(Spacer(1, 20))
            
            if summaries_data:
                # Quick stats
                total_days = len(summaries_data)
                avg_calories = sum(s.total_calories for s in summaries_data) / total_days
                avg_protein = sum(s.total_protein for s in summaries_data) / total_days
                total_meals = sum(s.meals_count for s in summaries_data)
                
                stats_data = [
                    ['Metric', 'Value'],
                    ['Days Tracked', str(total_days)],
                    ['Total Meals', str(total_meals)],
                    ['Avg Daily Calories', f"{avg_calories:.0f}"],
                    ['Avg Daily Protein', f"{avg_protein:.1f}g"]
                ]
                
                stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(stats_table)
                story.append(Spacer(1, 20))
                
                # Daily breakdown
                story.append(Paragraph("Daily Breakdown", self.heading_style))
                
                daily_data = [['Date', 'Meals', 'Calories', 'Protein']]
                for summary in reversed(summaries_data[-7:]):  # Last 7 days
                    daily_data.append([
                        summary.date.strftime('%m/%d'),
                        str(summary.meals_count),
                        f"{summary.total_calories:.0f}",
                        f"{summary.total_protein:.1f}g"
                    ])
                
                daily_table = Table(daily_data, colWidths=[1*inch, 1*inch, 1.5*inch, 1.5*inch])
                daily_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#A23B72')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(daily_table)
            else:
                story.append(Paragraph("No nutrition data available for this period.", self.body_style))
            
            # Build PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            print(f"Quick PDF generation error: {e}")
            raise e
