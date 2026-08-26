# TracePass code note: This module implements the config.py part of the application.
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


# Code explanation: Define the Config data model or application component used by TracePass.
class Config:
    """Base config. Never hardcode secrets here — everything comes from env."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB upload cap
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    WTF_CSRF_ENABLED = True


# Code explanation: Define the Development Config data model or application component used by TracePass.
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'tracepass_dev.db')}"
    )


# Code explanation: Define the Testing Config data model or application component used by TracePass.
class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Code explanation: Define the Production Config data model or application component used by TracePass.
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Code explanation: Implement the `validate` operation used by this part of TracePass.
    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY or cls.SECRET_KEY == "dev-key-change-me":
            raise RuntimeError("Production SECRET_KEY must be set to a strong random value")
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("Production DATABASE_URL must be configured")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
