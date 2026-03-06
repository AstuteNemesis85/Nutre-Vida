"""
Database migration script for notification system
Adds new fields to User table and creates NotificationLog table
"""

from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import Base
import sys

def run_migration():
    """Run the notification system migration"""
    try:
        # Create engine
        engine = create_engine(settings.database_url)
        
        print("🔄 Starting notification system migration...")
        
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = "sqlite" in settings.database_url.lower()
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("📋 Adding new columns to users table...")
                
                if is_sqlite:
                    # SQLite ALTER TABLE syntax
                    migration_queries = [
                        "ALTER TABLE users ADD COLUMN phone_number VARCHAR",
                        "ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT FALSE",
                        "ALTER TABLE users ADD COLUMN phone_otp VARCHAR",
                        "ALTER TABLE users ADD COLUMN phone_otp_expires DATETIME",
                        "ALTER TABLE users ADD COLUMN notification_preferences JSON",
                        "ALTER TABLE users ADD COLUMN last_meal_time DATETIME"
                    ]
                else:
                    # PostgreSQL ALTER TABLE syntax
                    migration_queries = [
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR UNIQUE",
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE",
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_otp VARCHAR",
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_otp_expires TIMESTAMP WITH TIME ZONE",
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preferences JSON",
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_meal_time TIMESTAMP WITH TIME ZONE"
                    ]
                
                # Execute migration queries
                for query in migration_queries:
                    try:
                        conn.execute(text(query))
                        print(f"✅ Executed: {query}")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                            print(f"⚠️  Column already exists: {query}")
                        else:
                            print(f"❌ Error executing {query}: {e}")
                            raise e
                
                print("📋 Creating notification_logs table...")
                
                # Create notification_logs table
                if is_sqlite:
                    create_notification_table = """
                    CREATE TABLE IF NOT EXISTS notification_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        notification_type VARCHAR NOT NULL,
                        channel VARCHAR NOT NULL,
                        status VARCHAR DEFAULT 'pending',
                        message_content TEXT,
                        twilio_sid VARCHAR,
                        error_message TEXT,
                        scheduled_for DATETIME,
                        sent_at DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                    """
                else:
                    create_notification_table = """
                    CREATE TABLE IF NOT EXISTS notification_logs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        notification_type VARCHAR NOT NULL,
                        channel VARCHAR NOT NULL,
                        status VARCHAR DEFAULT 'pending',
                        message_content TEXT,
                        twilio_sid VARCHAR,
                        error_message TEXT,
                        scheduled_for TIMESTAMP WITH TIME ZONE,
                        sent_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                    """
                
                conn.execute(text(create_notification_table))
                print("✅ Created notification_logs table")
                
                # Set default notification preferences for existing users
                print("📋 Setting default notification preferences for existing users...")
                
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
                
                if is_sqlite:
                    import json
                    update_preferences = f"""
                    UPDATE users 
                    SET notification_preferences = '{json.dumps(default_preferences)}'
                    WHERE notification_preferences IS NULL
                    """
                else:
                    update_preferences = f"""
                    UPDATE users 
                    SET notification_preferences = '{default_preferences}'::json
                    WHERE notification_preferences IS NULL
                    """
                
                result = conn.execute(text(update_preferences))
                print(f"✅ Updated notification preferences for {result.rowcount} users")
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
                # Print summary
                print("\n📊 Migration Summary:")
                print("✅ Added phone_number column to users table")
                print("✅ Added phone_verified column to users table")
                print("✅ Added phone_otp and phone_otp_expires columns to users table")
                print("✅ Added notification_preferences column to users table")
                print("✅ Added last_meal_time column to users table")
                print("✅ Created notification_logs table")
                print("✅ Set default notification preferences for existing users")
                
                print("\n🎉 Your FITKIT app now supports:")
                print("📱 WhatsApp notifications via Twilio")
                print("📧 Email notifications with PDF reports")
                print("⏰ Automated meal reminders")
                print("📊 Daily, weekly, and monthly summaries")
                print("🔐 Phone number verification with OTP")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_migration_status():
    """Check if migration has already been applied"""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if phone_number column exists
            if "sqlite" in settings.database_url.lower():
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
            else:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                """))
                columns = [row[0] for row in result.fetchall()]
            
            has_phone_number = 'phone_number' in columns
            
            # Check if notification_logs table exists
            if "sqlite" in settings.database_url.lower():
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='notification_logs'
                """))
            else:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'notification_logs'
                """))
            
            has_notification_table = len(result.fetchall()) > 0
            
            return has_phone_number and has_notification_table
            
    except Exception as e:
        print(f"❌ Error checking migration status: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FITKIT Notification System Migration")
    print("=" * 50)
    
    # Check current status
    if check_migration_status():
        print("✅ Migration has already been applied!")
        print("Your database is up to date with notification system features.")
        sys.exit(0)
    
    print("📋 Migration needed. Starting migration process...")
    
    # Confirm before proceeding
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        proceed = True
    else:
        response = input("\n⚠️  This will modify your database. Continue? (y/N): ")
        proceed = response.lower() in ['y', 'yes']
    
    if not proceed:
        print("❌ Migration cancelled by user")
        sys.exit(1)
    
    # Run migration
    success = run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your .env file with Twilio and email credentials")
        print("2. Restart your FITKIT application")
        print("3. Users can now verify their phone numbers in the app")
        print("4. Automated notifications will start working")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)
