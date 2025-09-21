# config.py
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')  # Pull SECRET_KEY from the environment
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Set to False to avoid overhead

class ProductionConfig(Config):
    """Production-specific configuration."""
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_SECURE = True  # Send cookies only over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Cookies not accessible via JavaScript
    SESSION_COOKIE_SAMESITE = 'None'  # Control when cookies are sent, adjust to 'Strict' if needed
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Get the database URL from environment
    DEBUG = False  # Ensure debug mode is off in production

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    SESSION_COOKIE_SECURE = False  # Don't need HTTPS locally
    SESSION_COOKIE_HTTPONLY = True  # Cookies not accessible via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:1478@localhost/jat')  # Default to local DB if not set
    DEBUG = True  # Enable debug mode
