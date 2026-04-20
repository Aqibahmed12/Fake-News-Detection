"""
Result Store — Persistence helpers for submissions.

Dual-write strategy
-------------------
Every prediction is persisted to **both** backends:

1. SQLAlchemy ORM  → local SQLite (dev) or Supabase PostgreSQL (prod via
   SUPABASE_DB_URL).  This is the primary store used by all existing ORM queries.

2. Supabase SDK    → ``predictions`` table via the supabase-py REST client.
   This enables Supabase-native features: Realtime, Row-Level Security, the
   Supabase Studio dashboard, and the dedicated ``/api/v1/history/supabase``
   endpoint.

If the Supabase SDK write fails it is logged as a warning and the request
continues normally — the ORM write is the source of truth.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from app.extensions import db
from app.models.submission import Submission

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_result(
    result: Dict[str, Any],
    input_text: Optional[str] = None,
    input_url: Optional[str] = None,
    source_type: str = "text",
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
) -> Submission:
    """
    Persist a detection result and return the Submission ORM object.

    The row is written to the SQLAlchemy-managed database (primary) and
    mirrored to the Supabase ``predictions`` table via the SDK (secondary).
    """
    features = result.get("features")
    features_json = json.dumps(features) if features else None

    # --- Primary: SQLAlchemy -------------------------------------------------
    sub = Submission(
        input_text=input_text[:10_000] if input_text else None,
        input_url=input_url,
        source_type=source_type,
        score=result.get("score"),
        label=result.get("label"),
        confidence=result.get("confidence"),
        features_json=features_json,
        model_used=result.get("model_used", "logistic"),
        processing_ms=result.get("processing_ms"),
        user_id=user_id,
        api_key_id=api_key_id,
    )
    db.session.add(sub)
    db.session.commit()

    # --- Secondary: Supabase SDK (non-fatal) ---------------------------------
    try:
        from app.supabase_client import sb_save_prediction
        sb_save_prediction(
            result_id=sub.id,          # keep IDs in sync
            user_id=user_id,
            api_key_id=api_key_id,
            input_text=input_text,
            input_url=input_url,
            source_type=source_type,
            score=result.get("score"),
            label=result.get("label"),
            confidence=result.get("confidence"),
            features_json=features_json,
            model_used=result.get("model_used", "logistic"),
            processing_ms=result.get("processing_ms"),
        )
    except Exception as exc:
        logger.warning("[result_store] Supabase mirror write failed: %s", exc)

    return sub


# ---------------------------------------------------------------------------
# Read — ORM-backed (default)
# ---------------------------------------------------------------------------

def get_result(result_id: str) -> Optional[Submission]:
    """Fetch a single submission by ID from the primary (ORM) store."""
    return db.session.get(Submission, result_id)


def get_history(
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Submission]:
    """Fetch paginated history from the primary (ORM) store."""
    q = Submission.query
    if user_id is not None:
        q = q.filter_by(user_id=user_id)
    if api_key_id is not None:
        q = q.filter_by(api_key_id=api_key_id)
    return q.order_by(Submission.created_at.desc()).limit(limit).offset(offset).all()


def get_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Return aggregate statistics from the primary (ORM) store."""
    q = Submission.query
    if user_id is not None:
        q = q.filter_by(user_id=user_id)

    total = q.count()
    if total == 0:
        return {"total": 0, "avg_score": 0, "label_counts": {}, "recent_7_days": 0}

    rows = q.all()
    scores = [r.score for r in rows if r.score is not None]
    label_counts: Dict[str, int] = {}
    for r in rows:
        if r.label:
            label_counts[r.label] = label_counts.get(r.label, 0) + 1

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent = sum(
        1 for r in rows
        if r.created_at and r.created_at.replace(tzinfo=timezone.utc) >= cutoff
    )

    return {
        "total": total,
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
        "label_counts": label_counts,
        "recent_7_days": recent,
    }


def purge_expired(days: int = 30) -> int:
    """Delete submissions older than ``days``.  Returns the count deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    count = Submission.query.filter(Submission.created_at < cutoff).delete()
    db.session.commit()
    return count
