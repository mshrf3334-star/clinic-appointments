import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-please")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///clinic.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REMINDERS_ENABLED = os.getenv("REMINDERS_ENABLED", "false").lower() == "true"
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM = os.getenv("TWILIO_FROM")
