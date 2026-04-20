"""
REST API — Results & History Endpoints
GET  /api/v1/result/<id>
GET  /api/v1/history
GET  /api/v1/history/supabase   ← Supabase-SDK-native history
GET  /api/v1/stats/supabase     ← Supabase-SDK-native aggregate stats
"""
import json
from flask import request, jsonify, g
from app.api import api_bp
from app.api.detect import require_auth
from app.services.result_store import get_result, get_history


# ---------------------------------------------------------------------------
# ORM-backed endpoints (existing)
# ---------------------------------------------------------------------------

@api_bp.route("/result/<result_id>", methods=["GET"])
@require_auth
def get_single_result(result_id: str):
    """Fetch a single prediction by ID (primary ORM store)."""
    sub = get_result(result_id)
    if not sub:
        return jsonify({"error": "Result not found"}), 404

    # Users can only see their own results
    user_id = getattr(g, "user_id", None)
    if user_id and sub.user_id and sub.user_id != user_id:
        return jsonify({"error": "Access denied"}), 403

    d = sub.to_dict(include_text=True)
    if sub.features_json:
        try:
            d["features"] = json.loads(sub.features_json)
        except Exception:
            d["features"] = []
    return jsonify(d), 200


@api_bp.route("/history", methods=["GET"])
@require_auth
def history():
    """Fetch paginated history from the primary (ORM) store."""
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    user_id = getattr(g, "user_id", None)
    api_key_id = getattr(g, "api_key_id", None)

    subs = get_history(user_id=user_id, api_key_id=api_key_id, limit=limit, offset=offset)
    return jsonify({
        "items": [s.to_dict() for s in subs],
        "count": len(subs),
        "limit": limit,
        "offset": offset,
        "source": "orm",
    }), 200


# ---------------------------------------------------------------------------
# Supabase-SDK-native endpoints (new)
# ---------------------------------------------------------------------------

@api_bp.route("/history/supabase", methods=["GET"])
@require_auth
def history_supabase():
    """
    Fetch paginated prediction history directly from the Supabase
    ``predictions`` table via the supabase-py REST client.

    Query params
    ------------
    limit  : int  (default 20, max 100)
    offset : int  (default 0)

    This endpoint bypasses SQLAlchemy entirely — useful for verifying
    Supabase connectivity and for dashboards that benefit from Supabase
    Realtime / Row-Level Security.
    """
    from app.supabase_client import sb_fetch_history, get_supabase_client

    client = get_supabase_client()
    if client is None:
        return jsonify({
            "error": "Supabase client is not configured. "
                     "Set SUPABASE_URL and SUPABASE_ANON_KEY in your environment.",
            "source": "supabase",
        }), 503

    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    user_id = getattr(g, "user_id", None)
    api_key_id = getattr(g, "api_key_id", None)

    rows = sb_fetch_history(
        user_id=user_id,
        api_key_id=api_key_id,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        "items": rows,
        "count": len(rows),
        "limit": limit,
        "offset": offset,
        "source": "supabase",
    }), 200


@api_bp.route("/stats/supabase", methods=["GET"])
@require_auth
def stats_supabase():
    """
    Return aggregate prediction statistics fetched directly from Supabase.

    Response keys: total, avg_score, label_counts, recent_7_days.
    """
    from app.supabase_client import sb_fetch_stats, get_supabase_client

    client = get_supabase_client()
    if client is None:
        return jsonify({
            "error": "Supabase client is not configured.",
            "source": "supabase",
        }), 503

    user_id = getattr(g, "user_id", None)
    stats = sb_fetch_stats(user_id=user_id)
    stats["source"] = "supabase"
    return jsonify(stats), 200
