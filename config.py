import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _build_database_uri() -> str:
    """
    Priority order for database URL:
    1. SUPABASE_DB_URL  — Supabase direct / transaction-pooler PostgreSQL URL
    2. DATABASE_URL     — any other PostgreSQL or SQLite URL
    3. Fallback         — local SQLite
    """
    url = (
        os.environ.get("SUPABASE_DB_URL")
        or os.environ.get("DATABASE_URL")
    )
    if url:
        # SQLAlchemy requires 'postgresql+psycopg2://' not 'postgres://'
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    return f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'fakenews.db')}"


def _engine_options() -> dict:
    uri = _build_database_uri()
    opts = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    if not uri.startswith("sqlite"):
        # Keep connections alive through Supabase's PgBouncer
        opts["connect_args"] = {
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    return opts


class Config:
    # Core
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod-xK9#mP2@")
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options()

    # Supabase SDK credentials (for the supabase-py client)
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-prod-yL8$nQ3!")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;60 per hour"
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "memory://")

    # WTF CSRF
    WTF_CSRF_ENABLED = True

    # Model paths
    MODELS_DIR = os.path.join(BASE_DIR, "models_cache")
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # Submission settings
    MIN_TEXT_LENGTH = 50
    MAX_TEXT_LENGTH = 10_000
    MAX_BATCH_SIZE = 50
    TEXT_RETENTION_DAYS = 30


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
