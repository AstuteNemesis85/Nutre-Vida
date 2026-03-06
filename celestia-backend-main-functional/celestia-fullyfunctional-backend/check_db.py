import sqlite3

conn = sqlite3.connect('fitkit.db')
cursor = conn.cursor()

print("📋 Checking database structure...")
print("=" * 40)

# Check users table
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Users table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n" + "=" * 40)

# Check if notification_logs table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_logs'")
result = cursor.fetchone()
if result:
    print("✅ notification_logs table exists")
    cursor.execute("PRAGMA table_info(notification_logs)")
    columns = cursor.fetchall()
    print("Notification_logs table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
else:
    print("❌ notification_logs table does not exist")

conn.close()
