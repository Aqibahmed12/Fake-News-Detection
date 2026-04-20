"""
Web UI — Dashboard routes for registered users.
"""
import json
import csv
import io
from flask import render_template, redirect, url_for, Response, current_app
from flask_login import login_required, current_user

from app.web import web_bp
from app.services.result_store import get_history, get_stats


@web_bp.route("/dashboard")
@login_required
def dashboard_view():
    history = get_history(user_id=current_user.id, limit=50)
    stats = get_stats(user_id=current_user.id)

    # Build chart data
    label_order = ["REAL", "LIKELY_REAL", "UNCERTAIN", "LIKELY_FAKE", "FAKE"]
    label_counts = [stats["label_counts"].get(l, 0) for l in label_order]

    return render_template(
        "dashboard.html",
        history=history,
        stats=stats,
        label_order=label_order,
        label_counts=label_counts,
    )


@web_bp.route("/dashboard/export")
@login_required
def export_csv():
    """Export user's submission history as CSV."""
    history = get_history(user_id=current_user.id, limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["result_id", "score", "label", "confidence", "model_used", "processing_ms", "timestamp", "source_type"])
    for sub in history:
        writer.writerow([
            sub.id, sub.score, sub.label, sub.confidence,
            sub.model_used, sub.processing_ms,
            sub.created_at.isoformat() if sub.created_at else "",
            sub.source_type,
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=fakenews_history.csv"},
    )
