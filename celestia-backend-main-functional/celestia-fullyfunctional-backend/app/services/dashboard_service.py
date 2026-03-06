import calendar
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models.db_models import DailySummary, Meal, User
from sqlalchemy import and_, extract, func
from sqlalchemy.orm import Session


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_meal_calendar_info(self, meal_id: int) -> bool:
        """Update meal with calendar information (date, time, day of week)"""
        try:
            meal = self.db.query(Meal).filter(Meal.id == meal_id).first()
            if not meal:
                return False
            
            now = datetime.now()
            meal.upload_date = now.date()
            meal.upload_time = now
            meal.day_of_week = now.strftime("%A")  # Monday, Tuesday, etc.
            
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating meal calendar info: {e}")
            self.db.rollback()
            return False
    
    def create_or_update_daily_summary(self, user_id: int, target_date: date = None) -> Dict[str, Any]:
        """Create or update daily summary for a user"""
        if not target_date:
            target_date = date.today()
        
        try:
            # Get all meals for the day
            meals = self.db.query(Meal).filter(
                and_(
                    Meal.user_id == user_id,
                    Meal.upload_date == target_date
                )
            ).all()
            
            # Calculate totals
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            total_fiber = 0
            meals_count = len(meals)
            
            for meal in meals:
                if meal.analysis_data:
                    total_calories += meal.analysis_data.get("total_calories", 0)
                    total_protein += meal.analysis_data.get("total_protein", 0)
                    total_carbs += meal.analysis_data.get("total_carbs", 0)
                    total_fat += meal.analysis_data.get("total_fat", 0)
                    total_fiber += meal.analysis_data.get("total_fiber", 0)
            
            # Get user goals
            user = self.db.query(User).filter(User.id == user_id).first()
            daily_goals = user.daily_goals if user and user.daily_goals else {}
            
            goal_calories = daily_goals.get("calories", 2000)
            goal_protein = daily_goals.get("protein", 50)
            
            # Check goal achievement
            goal_calories_achieved = total_calories >= goal_calories * 0.9  # 90% threshold
            goal_protein_achieved = total_protein >= goal_protein * 0.9
            
            # Create or update daily summary
            summary = self.db.query(DailySummary).filter(
                and_(
                    DailySummary.user_id == user_id,
                    DailySummary.date == target_date
                )
            ).first()
            
            if summary:
                # Update existing
                summary.total_calories = total_calories
                summary.total_protein = total_protein
                summary.total_carbs = total_carbs
                summary.total_fat = total_fat
                summary.total_fiber = total_fiber
                summary.meals_count = meals_count
                summary.goal_calories_achieved = goal_calories_achieved
                summary.goal_protein_achieved = goal_protein_achieved
                summary.updated_at = datetime.now()
            else:
                # Create new
                summary = DailySummary(
                    user_id=user_id,
                    date=target_date,
                    total_calories=total_calories,
                    total_protein=total_protein,
                    total_carbs=total_carbs,
                    total_fat=total_fat,
                    total_fiber=total_fiber,
                    meals_count=meals_count,
                    goal_calories_achieved=goal_calories_achieved,
                    goal_protein_achieved=goal_protein_achieved
                )
                self.db.add(summary)
            
            self.db.commit()
            
            return {
                "date": target_date.isoformat(),
                "total_calories": total_calories,
                "total_protein": total_protein,
                "total_carbs": total_carbs,
                "total_fat": total_fat,
                "total_fiber": total_fiber,
                "meals_count": meals_count,
                "goal_calories_achieved": goal_calories_achieved,
                "goal_protein_achieved": goal_protein_achieved,
                "goals": {
                    "calories": goal_calories,
                    "protein": goal_protein
                }
            }
            
        except Exception as e:
            print(f"Error creating daily summary: {e}")
            self.db.rollback()
            return {}
    
    def get_daily_dashboard(self, user_id: int, target_date: date = None) -> Dict[str, Any]:
        """Get today's dashboard data"""
        if not target_date:
            target_date = date.today()
        
        # Ensure daily summary is up to date
        summary_data = self.create_or_update_daily_summary(user_id, target_date)
        
        # Get meals for the day with breakdown by meal type
        meals = self.db.query(Meal).filter(
            and_(
                Meal.user_id == user_id,
                Meal.upload_date == target_date
            )
        ).order_by(Meal.upload_time).all()
        
        meal_breakdown = {
            "breakfast": {"count": 0, "calories": 0},
            "lunch": {"count": 0, "calories": 0},
            "dinner": {"count": 0, "calories": 0},
            "snack": {"count": 0, "calories": 0}
        }
        
        for meal in meals:
            meal_type = self.determine_meal_type(meal.upload_time.time()) if meal.upload_time else "snack"
            if meal.analysis_data:
                calories = meal.analysis_data.get("total_calories", 0)
                meal_breakdown[meal_type]["count"] += 1
                meal_breakdown[meal_type]["calories"] += calories
        
        return {
            **summary_data,
            "meal_breakdown": meal_breakdown,
            "day_of_week": target_date.strftime("%A"),
            "date_formatted": target_date.strftime("%B %d, %Y")
        }
    
    def get_weekly_dashboard(self, user_id: int, start_date: date = None) -> Dict[str, Any]:
        """Get weekly dashboard data"""
        if not start_date:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())  # Start of week (Monday)
        
        end_date = start_date + timedelta(days=6)  # End of week (Sunday)
        
        # Get daily summaries for the week
        summaries = self.db.query(DailySummary).filter(
            and_(
                DailySummary.user_id == user_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date
            )
        ).order_by(DailySummary.date).all()
        
        # Calculate weekly totals and averages
        total_calories = sum(s.total_calories for s in summaries)
        total_protein = sum(s.total_protein for s in summaries)
        total_carbs = sum(s.total_carbs for s in summaries)
        total_fat = sum(s.total_fat for s in summaries)
        total_meals = sum(s.meals_count for s in summaries)
        
        days_with_data = len(summaries)
        avg_calories = total_calories / days_with_data if days_with_data > 0 else 0
        avg_protein = total_protein / days_with_data if days_with_data > 0 else 0
        
        # Goal achievement stats
        days_calories_achieved = sum(1 for s in summaries if s.goal_calories_achieved)
        days_protein_achieved = sum(1 for s in summaries if s.goal_protein_achieved)
        
        # Daily breakdown
        daily_data = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_summary = next((s for s in summaries if s.date == current_date), None)
            
            daily_data.append({
                "date": current_date.isoformat(),
                "day_name": current_date.strftime("%A"),
                "calories": day_summary.total_calories if day_summary else 0,
                "protein": day_summary.total_protein if day_summary else 0,
                "meals_count": day_summary.meals_count if day_summary else 0,
                "goals_achieved": {
                    "calories": day_summary.goal_calories_achieved if day_summary else False,
                    "protein": day_summary.goal_protein_achieved if day_summary else False
                }
            })
        
        return {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "totals": {
                "calories": total_calories,
                "protein": total_protein,
                "carbs": total_carbs,
                "fat": total_fat,
                "meals": total_meals
            },
            "averages": {
                "calories": round(avg_calories, 1),
                "protein": round(avg_protein, 1)
            },
            "goal_achievement": {
                "calories_days": days_calories_achieved,
                "protein_days": days_protein_achieved,
                "total_days": days_with_data
            },
            "daily_data": daily_data
        }
    
    def get_monthly_dashboard(self, user_id: int, year: int = None, month: int = None) -> Dict[str, Any]:
        """Get monthly dashboard data"""
        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        
        # Get first and last day of month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Get daily summaries for the month
        summaries = self.db.query(DailySummary).filter(
            and_(
                DailySummary.user_id == user_id,
                DailySummary.date >= first_day,
                DailySummary.date <= last_day
            )
        ).order_by(DailySummary.date).all()
        
        # Calculate monthly totals and averages
        total_calories = sum(s.total_calories for s in summaries)
        total_protein = sum(s.total_protein for s in summaries)
        total_carbs = sum(s.total_carbs for s in summaries)
        total_fat = sum(s.total_fat for s in summaries)
        total_meals = sum(s.meals_count for s in summaries)
        
        days_with_data = len(summaries)
        avg_calories = total_calories / days_with_data if days_with_data > 0 else 0
        avg_protein = total_protein / days_with_data if days_with_data > 0 else 0
        
        # Goal achievement stats
        days_calories_achieved = sum(1 for s in summaries if s.goal_calories_achieved)
        days_protein_achieved = sum(1 for s in summaries if s.goal_protein_achieved)
        
        # Weekly breakdown
        weekly_data = []
        current_date = first_day
        week_num = 1
        
        while current_date <= last_day:
            week_start = current_date
            week_end = min(current_date + timedelta(days=6), last_day)
            
            week_summaries = [s for s in summaries if week_start <= s.date <= week_end]
            week_calories = sum(s.total_calories for s in week_summaries)
            week_protein = sum(s.total_protein for s in week_summaries)
            week_meals = sum(s.meals_count for s in week_summaries)
            
            weekly_data.append({
                "week_number": week_num,
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat(),
                "calories": week_calories,
                "protein": week_protein,
                "meals": week_meals,
                "days_tracked": len(week_summaries)
            })
            
            current_date = week_end + timedelta(days=1)
            week_num += 1
        
        return {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "totals": {
                "calories": total_calories,
                "protein": total_protein,
                "carbs": total_carbs,
                "fat": total_fat,
                "meals": total_meals
            },
            "averages": {
                "calories": round(avg_calories, 1),
                "protein": round(avg_protein, 1)
            },
            "goal_achievement": {
                "calories_days": days_calories_achieved,
                "protein_days": days_protein_achieved,
                "total_days": days_with_data,
                "calories_percentage": round((days_calories_achieved / days_with_data * 100), 1) if days_with_data > 0 else 0,
                "protein_percentage": round((days_protein_achieved / days_with_data * 100), 1) if days_with_data > 0 else 0
            },
            "weekly_data": weekly_data,
            "days_in_month": calendar.monthrange(year, month)[1],
            "days_tracked": days_with_data
        }
    
    def determine_meal_type(self, meal_time) -> str:
        """Determine meal type based on time of day"""
        hour = meal_time.hour
        
        if 5 <= hour < 11:
            return "breakfast"
        elif 11 <= hour < 16:
            return "lunch"
        elif 16 <= hour < 21:
            return "dinner"
        else:
            return "snack"
    
    def set_user_goals(self, user_id: int, goals: Dict[str, Any]) -> bool:
        """Set daily goals for a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Validate and set goals
            daily_goals = {
                "calories": goals.get("calories", 2000),
                "protein": goals.get("protein", 50),
                "carbs": goals.get("carbs", 250),
                "fat": goals.get("fat", 65),
                "fiber": goals.get("fiber", 25)
            }
            
            user.daily_goals = daily_goals
            user.updated_at = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error setting user goals: {e}")
            self.db.rollback()
            return False
    
    def get_meal_history_with_calendar(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get meal history with calendar information"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            meals = self.db.query(Meal).filter(
                and_(
                    Meal.user_id == user_id,
                    Meal.upload_date >= start_date,
                    Meal.upload_date <= end_date
                )
            ).order_by(Meal.upload_time.desc()).all()
            
            meal_history = []
            for meal in meals:
                meal_data = {
                    "id": meal.id,
                    "upload_date": meal.upload_date.isoformat() if meal.upload_date else None,
                    "upload_time": meal.upload_time.isoformat() if meal.upload_time else None,
                    "day_of_week": meal.day_of_week,
                    "meal_type": self.determine_meal_type(meal.upload_time.time()) if meal.upload_time else "unknown",
                    "analysis_data": meal.analysis_data,
                    "created_at": meal.created_at.isoformat() if meal.created_at else None
                }
                meal_history.append(meal_data)
            
            return meal_history
            
        except Exception as e:
            print(f"Error getting meal history: {e}")
            return []
    
    def get_nutrition_insights(self, user_id: int, period: str = "7d") -> Dict[str, Any]:
        """Get comprehensive nutrition insights for health dashboard"""
        try:
            # Determine date range based on period
            end_date = date.today()
            
            if period == "7d":
                start_date = end_date - timedelta(days=7)
                period_name = "7 Days"
            elif period == "1m":
                start_date = end_date - timedelta(days=30)
                period_name = "1 Month"
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
                period_name = "3 Months"
            else:
                start_date = end_date - timedelta(days=7)
                period_name = "7 Days"
            
            # Get user goals
            user = self.db.query(User).filter(User.id == user_id).first()
            daily_goals = user.daily_goals if user and user.daily_goals else {
                "calories": 2000,
                "protein": 50,
                "carbs": 250,
                "fat": 65,
                "fiber": 25
            }
            
            # Get daily summaries for the period
            summaries = self.db.query(DailySummary).filter(
                and_(
                    DailySummary.user_id == user_id,
                    DailySummary.date >= start_date,
                    DailySummary.date <= end_date
                )
            ).order_by(DailySummary.date).all()
            
            days_count = (end_date - start_date).days + 1
            
            print(f"Found {len(summaries)} daily summaries for user {user_id} in period {period}")
            
            if not summaries:
                print(f"No summaries found, checking for meals directly...")
                # Check if there are any meals at all for this user
                meals = self.db.query(Meal).filter(
                    and_(
                        Meal.user_id == user_id,
                        Meal.upload_date >= start_date,
                        Meal.upload_date <= end_date
                    )
                ).all()
                
                print(f"Found {len(meals)} meals for user {user_id}")
                
                if meals:
                    # Create daily summaries for existing meals
                    for current_date in [start_date + timedelta(days=x) for x in range(days_count)]:
                        self.create_or_update_daily_summary(user_id, current_date)
                    
                    # Re-fetch summaries after creation
                    summaries = self.db.query(DailySummary).filter(
                        and_(
                            DailySummary.user_id == user_id,
                            DailySummary.date >= start_date,
                            DailySummary.date <= end_date
                        )
                    ).order_by(DailySummary.date).all()
                    
                    print(f"Created summaries, now have {len(summaries)} summaries")
                
                if not summaries:
                    # Return empty data structure if no data available
                    return {
                        "period": period_name,
                        "days_count": days_count,
                        "days_tracked": 0,
                        "stats": {
                            "total_meals": 0,
                            "avg_calories": 0,
                            "calories_goal_achievement": 0,
                            "protein_intake": 0
                        },
                        "macronutrients": {
                            "protein": 33,
                            "carbs": 34,
                            "fat": 33
                        },
                        "daily_trend": [],
                        "deficiencies": [],
                        "message": "No meal data found. Start analyzing your meals to see insights!"
                    }
            
            # Calculate totals and averages
            total_calories = sum(s.total_calories for s in summaries)
            total_protein = sum(s.total_protein for s in summaries)
            total_carbs = sum(s.total_carbs for s in summaries)
            total_fat = sum(s.total_fat for s in summaries)
            total_fiber = sum(s.total_fiber for s in summaries)
            total_meals = sum(s.meals_count for s in summaries)
            
            days_with_data = len(summaries)
            avg_calories = total_calories / days_with_data if days_with_data > 0 else 0
            avg_protein = total_protein / days_with_data if days_with_data > 0 else 0
            avg_carbs = total_carbs / days_with_data if days_with_data > 0 else 0
            avg_fat = total_fat / days_with_data if days_with_data > 0 else 0
            avg_fiber = total_fiber / days_with_data if days_with_data > 0 else 0
            
            # Goal achievement calculations
            days_calories_achieved = sum(1 for s in summaries if s.goal_calories_achieved)
            calories_goal_achievement = (days_calories_achieved / days_with_data * 100) if days_with_data > 0 else 0
            
            # Macronutrient distribution (percentages)
            total_macro_calories = (total_protein * 4) + (total_carbs * 4) + (total_fat * 9)
            macro_percentages = {
                "protein": round((total_protein * 4 / total_macro_calories * 100), 1) if total_macro_calories > 0 else 0,
                "carbs": round((total_carbs * 4 / total_macro_calories * 100), 1) if total_macro_calories > 0 else 0,
                "fat": round((total_fat * 9 / total_macro_calories * 100), 1) if total_macro_calories > 0 else 0
            }
            
            # Daily trend data for charts
            daily_trend = []
            for i in range(days_count):
                current_date = start_date + timedelta(days=i)
                day_summary = next((s for s in summaries if s.date == current_date), None)
                
                daily_trend.append({
                    "date": current_date.isoformat(),
                    "calories": day_summary.total_calories if day_summary else 0,
                    "protein": day_summary.total_protein if day_summary else 0,
                    "carbs": day_summary.total_carbs if day_summary else 0,
                    "fat": day_summary.total_fat if day_summary else 0
                })
            
            # Deficiency analysis
            deficiencies = []
            
            # Check protein deficiency
            protein_goal = daily_goals.get("protein", 50)
            if avg_protein < protein_goal * 0.8:  # Less than 80% of goal
                deficiency_percentage = round(((protein_goal - avg_protein) / protein_goal * 100), 1)
                deficiencies.append({
                    "nutrient": "Protein",
                    "severity": "high" if avg_protein < protein_goal * 0.6 else "moderate",
                    "message": f"You're getting {deficiency_percentage}% less protein than recommended",
                    "recommendation": "Consider adding lean meats, fish, eggs, or plant-based proteins to your meals"
                })
            
            # Check fiber deficiency
            fiber_goal = daily_goals.get("fiber", 25)
            if avg_fiber < fiber_goal * 0.7:  # Less than 70% of goal
                deficiency_percentage = round(((fiber_goal - avg_fiber) / fiber_goal * 100), 1)
                deficiencies.append({
                    "nutrient": "Fiber",
                    "severity": "moderate",
                    "message": f"Your fiber intake is {deficiency_percentage}% below recommended levels",
                    "recommendation": "Add more fruits, vegetables, whole grains, and legumes to your diet"
                })
            
            # Check calorie balance
            calorie_goal = daily_goals.get("calories", 2000)
            if avg_calories < calorie_goal * 0.8:
                deficiencies.append({
                    "nutrient": "Calories",
                    "severity": "moderate",
                    "message": "Your calorie intake may be too low for your goals",
                    "recommendation": "Consider adding healthy, nutrient-dense snacks between meals"
                })
            elif avg_calories > calorie_goal * 1.2:
                deficiencies.append({
                    "nutrient": "Calories",
                    "severity": "moderate", 
                    "message": "Your calorie intake is above your daily goal",
                    "recommendation": "Focus on portion control and nutrient-dense, lower-calorie foods"
                })
            
            return {
                "period": period_name,
                "days_count": days_count,
                "days_tracked": days_with_data,
                "stats": {
                    "total_meals": total_meals,
                    "avg_calories": round(avg_calories, 1),
                    "calories_goal_achievement": round(calories_goal_achievement, 1),
                    "protein_intake": round(avg_protein, 1)
                },
                "macronutrients": macro_percentages,
                "daily_trend": daily_trend,
                "deficiencies": deficiencies,
                "averages": {
                    "calories": round(avg_calories, 1),
                    "protein": round(avg_protein, 1),
                    "carbs": round(avg_carbs, 1),
                    "fat": round(avg_fat, 1),
                    "fiber": round(avg_fiber, 1)
                },
                "goals": daily_goals
            }
            
        except Exception as e:
            print(f"Error getting nutrition insights: {e}")
            return {
                "error": "Failed to fetch nutrition insights",
                "period": period,
                "stats": {},
                "macronutrients": {},
                "daily_trend": [],
                "deficiencies": []
            }
