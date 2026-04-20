import os
import logging
from flask import Flask
from config import get_config
from app.extensions import db, jwt, login_manager, limiter, csrf

logger = logging.getLogger(__name__)


def create_app(config_class=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )

    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Ensure instance & model dirs exist
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance"), exist_ok=True)
    os.makedirs(app.config["MODELS_DIR"], exist_ok=True)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # Log which database backend is active
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if "supabase" in db_uri or "pooler.supabase" in db_uri:
        backend = "Supabase (PostgreSQL via Transaction Pooler)"
    elif "postgresql" in db_uri or "postgres" in db_uri:
        backend = "PostgreSQL"
    else:
        backend = "SQLite (local)"
    app.logger.info(f"[DB] Using: {backend}")

    login_manager.login_view = "web.login"
    login_manager.login_message_category = "info"

    # Template filters
    @app.template_filter("score_color")
    def score_color_filter(score):
        if score is None:
            return "#94a3b8"
        if score >= 0.80: return "#22c55e"
        if score >= 0.60: return "#86efac"
        if score >= 0.40: return "#facc15"
        if score >= 0.20: return "#f97316"
        return "#ef4444"

    @app.template_global()
    def score_color(score):
        return score_color_filter(score)

    # Register blueprints
    from app.api import api_bp
    from app.web import web_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(web_bp)

    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Create DB tables (SQLAlchemy ORM)
    with app.app_context():
        db.create_all()
        _seed_admin(app)

        # Bootstrap Supabase predictions table (runs DDL once, idempotent)
        try:
            from app.supabase_client import ensure_tables, get_supabase_client
            ensure_tables(app)
            client = get_supabase_client()
            if client:
                app.logger.info("[Supabase] SDK client ready — predictions table bootstrapped.")
            else:
                app.logger.info(
                    "[Supabase] SDK client not configured (SUPABASE_URL/ANON_KEY missing). "
                    "Running in ORM-only mode."
                )
        except Exception as exc:
            app.logger.warning("[Supabase] Bootstrap error (non-fatal): %s", exc)

    return app


def _seed_admin(app):
    """Create a default admin user on first run."""
    from app.models.user import User
    with app.app_context():
        if User.query.filter_by(email="admin@fakenews.local").first() is None:
            admin = User(
                email="admin@fakenews.local",
                username="admin",
                role="admin",
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Default admin created: admin@fakenews.local / admin123")
