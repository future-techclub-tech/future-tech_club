import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

class Config:
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    SECRET_KEY = os.getenv("SECRET_KEY")
    if APP_ENV == "production" and (
        not SECRET_KEY
        or len(SECRET_KEY) < 32
        or SECRET_KEY == "change-this-to-a-long-random-secret"
    ):
        raise RuntimeError("Production requires a SECRET_KEY of at least 32 characters.")
    SECRET_KEY = SECRET_KEY or "development-only-change-me"
    BOOTSTRAP_ADMIN_USERNAME = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "24062231242187")
    BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    TEAM_INITIAL_PASSWORD = os.getenv("TEAM_INITIAL_PASSWORD")
    if APP_ENV == "production" and (
        not BOOTSTRAP_ADMIN_PASSWORD
        or len(BOOTSTRAP_ADMIN_PASSWORD) < 12
    ):
        raise RuntimeError("Production requires a unique BOOTSTRAP_ADMIN_PASSWORD of at least 12 characters.")
    if APP_ENV == "production" and TEAM_INITIAL_PASSWORD:
        raise RuntimeError("Production team accounts must use unique generated passwords.")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///future_tech_innovision.db"
    ).strip()
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql+psycopg://", 1
        )
    elif SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
    if APP_ENV == "production" and not SQLALCHEMY_DATABASE_URI.startswith(
        "postgresql+psycopg://"
    ):
        raise RuntimeError(
            "Production requires a persistent PostgreSQL DATABASE_URL."
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    MAX_CONTENT_LENGTH = 300 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    CERTIFICATE_PUBLIC_BASE_URL = (
        os.getenv("CERTIFICATE_PUBLIC_BASE_URL", "").strip().rstrip("/")
        or os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
    )
    TASK_EMAIL_SMTP_HOST = os.getenv("TASK_EMAIL_SMTP_HOST", "")
    TASK_EMAIL_SMTP_PORT = int(os.getenv("TASK_EMAIL_SMTP_PORT", "587"))
    TASK_EMAIL_SMTP_USERNAME = os.getenv("TASK_EMAIL_SMTP_USERNAME", "")
    TASK_EMAIL_SMTP_PASSWORD = os.getenv("TASK_EMAIL_SMTP_PASSWORD", "")
    TASK_EMAIL_FROM = os.getenv(
        "TASK_EMAIL_FROM", "future-techclub@orchidengg.ac.in"
    )
    TASK_CONTACT_PHONE = os.getenv("TASK_CONTACT_PHONE", "9834599110")
    TASK_SMS_AUTH_KEY = os.getenv("TASK_SMS_AUTH_KEY", "")
    TASK_SMS_TEMPLATE_ID = os.getenv("TASK_SMS_TEMPLATE_ID", "")
    TASK_SMS_VARIABLE_NAME = os.getenv("TASK_SMS_VARIABLE_NAME", "VAR1")
    TASK_SMS_COUNTRY_CODE = os.getenv("TASK_SMS_COUNTRY_CODE", "91")
    DEBUG = APP_ENV != "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_PROTECTION = "strong"
    SESSION_COOKIE_SECURE = os.getenv(
        "SESSION_COOKIE_SECURE", "true" if APP_ENV == "production" else "false"
    ).lower() == "true"
    if APP_ENV == "production" and not SESSION_COOKIE_SECURE:
        raise RuntimeError("Production requires SESSION_COOKIE_SECURE=true.")
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    WTF_CSRF_TIME_LIMIT = 3600
