#!/usr/bin/env python3
"""
Database migration script to add new columns to existing tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine, get_db
from app.models.db_models import Base

def migrate_database():
    """Add new columns to existing tables"""
    
    with engine.connect() as connection:
        # Start a transaction
        trans = connection.begin()
        
        try:
            print("Starting database migration...")
            
            # Add new columns to users table
            print("Adding new columns to users table...")
            try:
                connection.execute(text("ALTER TABLE users ADD COLUMN daily_goals JSON DEFAULT '{}'"))
                print("✓ Added daily_goals column to users table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ daily_goals column already exists in users table")
                else:
                    raise e
            
            try:
                connection.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
                print("✓ Added updated_at column to users table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ updated_at column already exists in users table")
                else:
                    raise e
            
            # Add new columns to meals table
            print("Adding new columns to meals table...")
            try:
                connection.execute(text("ALTER TABLE meals ADD COLUMN meal_type VARCHAR(50)"))
                print("✓ Added meal_type column to meals table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ meal_type column already exists in meals table")
                else:
                    raise e
            
            try:
                connection.execute(text("ALTER TABLE meals ADD COLUMN upload_date DATE"))
                print("✓ Added upload_date column to meals table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ upload_date column already exists in meals table")
                else:
                    raise e
            
            try:
                connection.execute(text("ALTER TABLE meals ADD COLUMN upload_time DATETIME"))
                print("✓ Added upload_time column to meals table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ upload_time column already exists in meals table")
                else:
                    raise e
            
            try:
                connection.execute(text("ALTER TABLE meals ADD COLUMN day_of_week VARCHAR(20)"))
                print("✓ Added day_of_week column to meals table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ day_of_week column already exists in meals table")
                else:
                    raise e
            
            try:
                connection.execute(text("ALTER TABLE meals ADD COLUMN updated_at DATETIME"))
                print("✓ Added updated_at column to meals table")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ updated_at column already exists in meals table")
                else:
                    raise e
            
            # Create daily_summaries table if it doesn't exist
            print("Creating daily_summaries table...")
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS daily_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        total_calories REAL DEFAULT 0.0,
                        total_protein REAL DEFAULT 0.0,
                        total_carbs REAL DEFAULT 0.0,
                        total_fat REAL DEFAULT 0.0,
                        total_fiber REAL DEFAULT 0.0,
                        meals_count INTEGER DEFAULT 0,
                        goal_calories_achieved BOOLEAN DEFAULT 0,
                        goal_protein_achieved BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                print("✓ Created daily_summaries table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✓ daily_summaries table already exists")
                else:
                    raise e
            
            # Update existing meals with current timestamp for upload_date and upload_time
            print("Updating existing meals with current timestamps...")
            connection.execute(text("""
                UPDATE meals 
                SET upload_date = date(created_at),
                    upload_time = created_at,
                    day_of_week = CASE cast(strftime('%w', created_at) as integer)
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END,
                    updated_at = created_at
                WHERE upload_date IS NULL OR upload_time IS NULL
            """))
            print("✓ Updated existing meals with calendar information")
            
            # Commit the transaction
            trans.commit()
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise e

if __name__ == "__main__":
    migrate_database()
