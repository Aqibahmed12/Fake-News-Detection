"""
Web UI Routes — Main views: index, submit, result, login, register, logout, admin.
"""
import json
from flask import (
    render_template, request, redirect, url_for,
    flash, current_app, jsonify, g, abort,
)
from flask_login import login_user, logout_user, login_required, current_user

from app.web import web_bp
from app.extensions import db, limiter
from app.models.user import User
from app.models.api_key import APIKey


def _get_engine():
    from app.services.ml_engine import MLEngine
    if not hasattr(current_app, "_ml_engine"):
        current_app._ml_engine = MLEngine(current_app.config["MODELS_DIR"])
    return current_app._ml_engine


# ------------------------------------------------------------------
# Home / Submit
# ------------------------------------------------------------------

@web_bp.route("/", methods=["GET"])
def index():
    stats = {}
    try:
        from app.services.result_store import get_stats
        stats = get_stats()
    except Exception:
        pass
    return render_template("index.html", stats=stats)


@web_bp.route("/detect", methods=["POST"])
@limiter.limit("30 per minute")
def detect():
    text = request.form.get("text", "").strip()
    url = request.form.get("url", "").strip()
    model_type = request.form.get("model", "logistic")
    source_type = request.form.get("source_type", "text")

    if source_type == "url" and url:
        from app.api.detect import _fetch_url
        text, err = _fetch_url(url)
        if err:
            flash(f"Could not fetch URL: {err}", "danger")
            return redirect(url_for("web.index"))
    elif source_type == "file":
        f = request.files.get("file")
        if f and f.filename:
            text = f.read().decode("utf-8", errors="ignore")

    min_len = current_app.config["MIN_TEXT_LENGTH"]
    max_len = current_app.config["MAX_TEXT_LENGTH"]
    if len(text) < min_len:
        flash(f"Text is too short. Please provide at least {min_len} characters.", "warning")
        return redirect(url_for("web.index"))
    if len(text) > max_len:
        text = text[:max_len]

    engine = _get_engine()
    if not engine.is_trained():
        flash("The ML model has not been trained yet. Please contact the administrator.", "danger")
        return redirect(url_for("web.index"))

    result = engine.predict(text, model_type=model_type, return_features=True)

    from app.services.result_store import save_result
    user_id = current_user.id if current_user.is_authenticated else None
    sub = save_result(
        result,
        input_text=text if source_type == "text" else None,
        input_url=url if source_type == "url" else None,
        source_type=source_type,
        user_id=user_id,
    )

    return redirect(url_for("web.result", result_id=sub.id))


@web_bp.route("/result/<result_id>")
def result(result_id: str):
    from app.services.result_store import get_result
    from app.services.ml_engine import LABEL_COLORS
    sub = get_result(result_id)
    if not sub:
        abort(404)

    features = []
    if sub.features_json:
        try:
            features = json.loads(sub.features_json)
        except Exception:
            pass

    color = LABEL_COLORS.get(sub.label, "#facc15")
    score_pct = int((sub.score or 0) * 100)

    return render_template(
        "result.html",
        sub=sub,
        features=features,
        color=color,
        score_pct=score_pct,
    )


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------

@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash("Welcome back!", "success")
            return redirect(url_for("web.dashboard_view"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html")


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not email or not username or not password:
            flash("All fields are required.", "warning")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
        else:
            user = User(email=email, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash("Account created! Welcome to TruthLens.", "success")
            return redirect(url_for("web.dashboard_view"))
    return render_template("auth/register.html")


@web_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("web.index"))


# ------------------------------------------------------------------
# Admin Panel
# ------------------------------------------------------------------

@web_bp.route("/admin")
@login_required
def admin():
    if not current_user.is_admin():
        abort(403)
    from app.services.result_store import get_stats
    from app.services.ml_engine import MLEngine
    import os, json

    stats = get_stats()
    engine = MLEngine(current_app.config["MODELS_DIR"])
    health = engine.health()

    # Load model metadata
    meta_path = os.path.join(current_app.config["MODELS_DIR"], "metadata.json")
    model_meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            model_meta = json.load(f)

    api_keys = APIKey.query.order_by(APIKey.created_at.desc()).all()
    users = User.query.order_by(User.created_at.desc()).limit(50).all()

    return render_template(
        "admin/panel.html",
        stats=stats,
        health=health,
        model_meta=model_meta,
        api_keys=api_keys,
        users=users,
    )


@web_bp.route("/admin/retrain", methods=["POST"])
@login_required
def admin_retrain():
    if not current_user.is_admin():
        abort(403)
    try:
        from train_model import train_and_save
        meta = train_and_save(
            current_app.config["MODELS_DIR"],
            current_app.config["DATA_DIR"],
        )
        # Reset cached engine
        if hasattr(current_app, "_ml_engine"):
            delattr(current_app, "_ml_engine")
        flash(f"Model retrained successfully! LR F1={meta.get('logistic_f1', 'N/A')}", "success")
    except Exception as e:
        flash(f"Retraining failed: {str(e)}", "danger")
    return redirect(url_for("web.admin"))


@web_bp.route("/admin/api-keys/create", methods=["POST"])
@login_required
def admin_create_key():
    if not current_user.is_admin():
        abort(403)
    name = request.form.get("name", "API Key").strip()
    user_id = int(request.form.get("user_id", current_user.id))
    raw, key_obj = APIKey.generate()
    key_obj.name = name
    key_obj.user_id = user_id
    db.session.add(key_obj)
    db.session.commit()
    flash(f"API Key created: {raw}  (copy it now — it won't be shown again)", "success")
    return redirect(url_for("web.admin"))


@web_bp.route("/admin/api-keys/<int:key_id>/revoke", methods=["POST"])
@login_required
def admin_revoke_key(key_id: int):
    if not current_user.is_admin():
        abort(403)
    key = APIKey.query.get_or_404(key_id)
    key.is_active = False
    db.session.commit()
    flash("API Key revoked.", "info")
    return redirect(url_for("web.admin"))
