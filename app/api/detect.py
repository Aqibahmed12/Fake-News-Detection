"""
REST API — Detection Endpoints
POST /api/v1/detect
POST /api/v1/detect/batch
GET  /api/v1/health
"""
import os
import time
import requests
from flask import request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from functools import wraps

from app.api import api_bp
from app.extensions import db, limiter
from app.models.api_key import APIKey
from app.models.submission import Submission


def _get_engine():
    """Lazy-load the ML engine, cached on the app context."""
    from app.services.ml_engine import MLEngine
    if not hasattr(current_app, "_ml_engine"):
        current_app._ml_engine = MLEngine(current_app.config["MODELS_DIR"])
    return current_app._ml_engine


def require_auth(f):
    """Accept either JWT Bearer token or X-API-Key header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            api_key = APIKey.verify(api_key_header)
            if not api_key:
                return jsonify({"error": "Invalid or inactive API key"}), 401
            # Update last used
            from datetime import datetime, timezone
            api_key.last_used_at = datetime.now(timezone.utc)
            db.session.commit()
            g.api_key_id = api_key.id
            g.user_id = api_key.user_id
            return f(*args, **kwargs)
        # Try JWT
        try:
            verify_jwt_in_request()
            g.user_id = int(get_jwt_identity())
            g.api_key_id = None
            return f(*args, **kwargs)
        except Exception:
            return jsonify({"error": "Authentication required"}), 401
    return decorated


@api_bp.route("/detect", methods=["POST"])
@limiter.limit("60 per minute")
@require_auth
def detect_single():
    """Submit a single text/url for detection."""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    url = data.get("url", "").strip()
    return_features = bool(data.get("return_features", False))
    model_type = data.get("model", "logistic")

    # Validate
    if not text and not url:
        return jsonify({"error": "Provide 'text' or 'url'"}), 400
    if text and url:
        return jsonify({"error": "'text' and 'url' are mutually exclusive"}), 400

    source_type = "text"
    if url:
        text, err = _fetch_url(url)
        if err:
            return jsonify({"error": err}), 422
        source_type = "url"

    min_len = current_app.config["MIN_TEXT_LENGTH"]
    max_len = current_app.config["MAX_TEXT_LENGTH"]
    if len(text) < min_len:
        return jsonify({"error": f"Text too short (min {min_len} chars)"}), 422
    if len(text) > max_len:
        return jsonify({"error": f"Text too long (max {max_len} chars)"}), 422

    engine = _get_engine()
    if not engine.is_trained():
        return jsonify({"error": "Model not trained yet. Contact admin."}), 503

    result = engine.predict(text, model_type=model_type, return_features=return_features)

    from app.services.result_store import save_result
    sub = save_result(
        result,
        input_text=text if source_type == "text" else None,
        input_url=url if source_type == "url" else None,
        source_type=source_type,
        user_id=getattr(g, "user_id", None),
        api_key_id=getattr(g, "api_key_id", None),
    )

    response = {
        "result_id": sub.id,
        "score": result["score"],
        "label": result["label"],
        "confidence": result["confidence"],
        "processing_ms": result["processing_ms"],
        "timestamp": sub.created_at.isoformat(),
    }
    if return_features:
        response["features"] = result.get("features", [])
    return jsonify(response), 200


@api_bp.route("/detect/batch", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth
def detect_batch():
    """Submit up to 50 items in one request."""
    data = request.get_json(force=True, silent=True) or {}
    items = data.get("items", [])
    max_batch = current_app.config["MAX_BATCH_SIZE"]

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"error": "'items' must be a non-empty array"}), 400
    if len(items) > max_batch:
        return jsonify({"error": f"Maximum batch size is {max_batch}"}), 400

    engine = _get_engine()
    if not engine.is_trained():
        return jsonify({"error": "Model not trained yet."}), 503

    from app.services.result_store import save_result
    results_out = []
    for idx, item in enumerate(items):
        text = item.get("text", "").strip() if isinstance(item, dict) else str(item).strip()
        if not text or len(text) < current_app.config["MIN_TEXT_LENGTH"]:
            results_out.append({"index": idx, "error": "Text too short"})
            continue
        text = text[:current_app.config["MAX_TEXT_LENGTH"]]
        result = engine.predict(text)
        sub = save_result(
            result, input_text=text, source_type="text",
            user_id=getattr(g, "user_id", None),
            api_key_id=getattr(g, "api_key_id", None),
        )
        results_out.append({
            "index": idx,
            "result_id": sub.id,
            "score": result["score"],
            "label": result["label"],
            "confidence": result["confidence"],
        })

    return jsonify({"results": results_out, "count": len(results_out)}), 200


@api_bp.route("/health", methods=["GET"])
def health():
    """Service health check — no auth required."""
    engine = _get_engine()
    h = engine.health()
    status = "ok" if h["trained"] else "degraded"
    return jsonify({
        "status": status,
        "model_trained": h["trained"],
        "models_available": {
            "logistic": h["trained"],
            "xgboost": h["xgboost_loaded"],
        },
    }), 200


def _fetch_url(url: str) -> tuple[str, str | None]:
    """Fetch and extract text from a public URL."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "FakeNewsDetector/1.0"})
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        # Extract main content
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:10_000], None
    except Exception as e:
        return "", f"Failed to fetch URL: {str(e)}"
