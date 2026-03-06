from app.database import engine
from sqlalchemy import text
import sys

try:
    with engine.connect() as conn:
        # Check if notification_logs table exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('notification_logs', 'users')
        """))
        tables = [row[0] for row in result.fetchall()]
        
        print('✅ Database connection successful!')
        print(f'📋 Found tables: {tables}')
        
        # Check if new columns exist in users table
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name IN ('phone_number', 'phone_verified', 'notification_preferences')
        """))
        columns = [row[0] for row in result.fetchall()]
        
        print(f'📱 New user columns: {columns}')
        
        if 'notification_logs' in tables and len(columns) >= 2:
            print('🎉 Migration completed successfully!')
        else:
            print('⚠️ Migration may be incomplete')
            
except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)
