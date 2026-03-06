from app.database import Base, engine
from app.models.db_models import User, Meal, DailySummary, NotificationLog

print('🗑️ Removing old database...')
import os
if os.path.exists('fitkit.db'):
    os.remove('fitkit.db')
    print('✅ Old database removed')

print('📋 Creating database tables...')
Base.metadata.create_all(bind=engine)
print('✅ Database tables created successfully!')

print('🔍 Verifying tables...')
import sqlite3
conn = sqlite3.connect('fitkit.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Created tables: {[table[0] for table in tables]}")

cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print(f"Users table has {len(columns)} columns including notification fields")

conn.close()
