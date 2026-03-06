from app.config import settings
import os

print("🔧 Configuration Test")
print("=" * 30)
print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL')}")
print(f"DATABASE_URL from settings: {settings.database_url}")
print(f"GOOGLE_API_KEY from env: {os.getenv('GOOGLE_API_KEY')}")
print(f"GOOGLE_API_KEY from settings: {settings.google_api_key}")
print(f"TWILIO_ACCOUNT_SID from env: {os.getenv('TWILIO_ACCOUNT_SID')}")
print(f"TWILIO_ACCOUNT_SID from settings: {settings.twilio_account_sid}")

if "postgresql" in settings.database_url:
    print("✅ Using PostgreSQL database")
else:
    print("❌ Using SQLite database (should be PostgreSQL)")
