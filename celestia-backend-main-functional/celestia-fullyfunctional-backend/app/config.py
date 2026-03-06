import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Twilio Configuration
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    
    # Email Configuration
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@fitkit.com")
    
    # JWT Secret for OTP tokens
    jwt_secret: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    
    # App Configuration
    app_name: str = os.getenv("APP_NAME", "FITKIT")
    app_url: str = os.getenv("APP_URL", "http://localhost:8000")

    class Config:
        env_file = ".env"

settings = Settings()
