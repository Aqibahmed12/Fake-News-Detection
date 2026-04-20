"""
Supabase Client — Singleton + Table Bootstrap + Typed Helpers
=============================================================

Usage
-----
    from app.supabase_client import get_supabase_client, ensure_tables
    from app.supabase_client import sb_save_prediction, sb_get_prediction, sb_fetch_history

The client is initialised once from Flask app-config (SUPABASE_URL / SUPABASE_ANON_KEY)
and thereafter cached.  All public helpers return plain dicts so callers have no
dependency on supabase-py internals.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal singleton
# ---------------------------------------------------------------------------
_client = None


def get_supabase_client():
    """
    Return an initialised ``supabase.Client``, or ``None`` if credentials
    are missing / the package is not installed.

    The instance is cached after the first successful creation so that
    subsequent calls are O(1) dict lookups.
    """
    global _client
    if _client is not None:
        return _client

    try:
        from flask import current_app
        url: str = current_app.config.get("SUPABASE_URL", "").strip()
        key: str = (
            current_app.config.get("SUPABASE_SERVICE_KEY", "").strip()
            or current_app.config.get("SUPABASE_ANON_KEY", "").strip()
        )
    except RuntimeError:
        # Called outside of Flask app context — skip silently
        return None

    if not url or not key:
        logger.warning(
            "[Supabase] SUPABASE_URL / SUPABASE_ANON_KEY not set. "
            "Supabase SDK features are disabled."
        )
        return None

    try:
        from supabase import create_client  # type: ignore
        _client = create_client(url, key)
        logger.info("[Supabase] Client initialised → %s", url)
        return _client
    except ImportError:
        logger.warning("[Supabase] supabase-py not installed. Run: pip install supabase>=2.3")
        return None
    except Exception as exc:
        logger.error("[Supabase] Client initialisation failed: %s", exc)
        return None


def reset_client() -> None:
    """Force re-initialisation on the next call (useful after credential rotation)."""
    global _client
    _client = None


# ---------------------------------------------------------------------------
# Table bootstrap
# ---------------------------------------------------------------------------

# DDL for the predictions table.  We use Supabase's REST API (PostgREST) for
# all reads/writes, so we need the table to exist first.
# `CREATE TABLE IF NOT EXISTS` is executed via the pg_query RPC function that
# Supabase exposes, or — if that RPC is not enabled — via the psycopg2 connection
# that SQLAlchemy already holds (fallback).
_PREDICTIONS_DDL = """
CREATE TABLE IF NOT EXISTS predictions (
    id            TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       INTEGER     NULL,
    api_key_id    INTEGER     NULL,
    input_text    TEXT        NULL,
    input_url     TEXT        NULL,
    source_type   TEXT        NOT NULL DEFAULT 'text',
    score         REAL        NULL,
    label         TEXT        NULL,
    confidence    REAL        NULL,
    features_json TEXT        NULL,
    model_used    TEXT        NOT NULL DEFAULT 'logistic',
    processing_ms INTEGER     NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS predictions_user_id_idx    ON predictions (user_id);
CREATE INDEX IF NOT EXISTS predictions_api_key_id_idx ON predictions (api_key_id);
CREATE INDEX IF NOT EXISTS predictions_created_at_idx ON predictions (created_at DESC);
"""


def ensure_tables(app=None) -> bool:
    """
    Ensure the ``predictions`` table (and its indexes) exist in Supabase.

    Strategy
    --------
    1. Try a direct psycopg2 connection via SQLAlchemy's engine.  This works
       when the app factory has already called ``db.init_app(app)`` **and**
       ``SUPABASE_DB_URL`` / ``DATABASE_URL`` points at PostgreSQL.
    2. If that fails (SQLite dev mode, or db not yet initialised), log clear
       guidance — the operator should run the DDL via the Supabase SQL Editor
       (file: migrations/create_predictions.sql).

    Returns ``True`` on success or when running against SQLite (no-op),
    ``False`` when the table could not be created automatically.
    """
    try:
        from app.extensions import db
        from sqlalchemy import text

        # db.engine is only available after db.init_app(app) has been called.
        engine = db.engine
        dialect = engine.dialect.name

        if dialect != "postgresql":
            logger.info(
                "[Supabase] ensure_tables: skipped for dialect '%s' (SQLite). "
                "Run migrations/create_predictions.sql in the Supabase SQL Editor.",
                dialect,
            )
            return True  # Nothing to do for SQLite

        with engine.connect() as conn:
            conn.execute(text(_PREDICTIONS_DDL))
            conn.commit()
        logger.info("[Supabase] ensure_tables: 'predictions' table ready (via psycopg2).")
        return True

    except Exception as exc:
        logger.warning(
            "[Supabase] ensure_tables via psycopg2 failed (%s). "
            "Please run migrations/create_predictions.sql in the Supabase SQL Editor.",
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Typed CRUD helpers
# ---------------------------------------------------------------------------

def sb_save_prediction(
    *,
    result_id: Optional[str] = None,
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    input_text: Optional[str] = None,
    input_url: Optional[str] = None,
    source_type: str = "text",
    score: Optional[float] = None,
    label: Optional[str] = None,
    confidence: Optional[float] = None,
    features_json: Optional[str] = None,
    model_used: str = "logistic",
    processing_ms: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Insert one prediction row into the Supabase ``predictions`` table.

    Returns the inserted row dict on success, or ``None`` if the client is
    unavailable or insertion fails (so callers can degrade gracefully).
    """
    client = get_supabase_client()
    if client is None:
        return None

    row: Dict[str, Any] = {
        "id": result_id or str(uuid.uuid4()),
        "user_id": user_id,
        "api_key_id": api_key_id,
        "input_text": input_text[:10_000] if input_text else None,
        "input_url": input_url,
        "source_type": source_type,
        "score": score,
        "label": label,
        "confidence": confidence,
        "features_json": features_json,
        "model_used": model_used,
        "processing_ms": processing_ms,
        # Supabase/PostgREST accepts ISO-8601 strings
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = (
            client.table("predictions")
            .insert(row)
            .execute()
        )
        data = response.data
        if data:
            logger.debug("[Supabase] Prediction saved: %s", row["id"])
            return data[0]
        logger.warning("[Supabase] sb_save_prediction: empty response data.")
        return None
    except Exception as exc:
        logger.error("[Supabase] sb_save_prediction failed: %s", exc)
        return None


def sb_get_prediction(result_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single prediction row by primary key.

    Returns a dict or ``None`` if not found / client unavailable.
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        response = (
            client.table("predictions")
            .select("*")
            .eq("id", result_id)
            .limit(1)
            .execute()
        )
        data = response.data
        return data[0] if data else None
    except Exception as exc:
        logger.error("[Supabase] sb_get_prediction(%s) failed: %s", result_id, exc)
        return None


def sb_fetch_history(
    *,
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Fetch prediction history from Supabase, ordered newest-first.

    Filters by ``user_id`` and/or ``api_key_id`` when provided.
    Returns a (possibly empty) list of row dicts.
    """
    client = get_supabase_client()
    if client is None:
        return []

    try:
        query = (
            client.table("predictions")
            .select(
                "id, user_id, score, label, confidence, model_used, "
                "processing_ms, source_type, input_url, created_at"
            )
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        if user_id is not None:
            query = query.eq("user_id", user_id)
        if api_key_id is not None:
            query = query.eq("api_key_id", api_key_id)

        response = query.execute()
        return response.data or []
    except Exception as exc:
        logger.error("[Supabase] sb_fetch_history failed: %s", exc)
        return []


def sb_fetch_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Return aggregate statistics from the ``predictions`` table.

    Because PostgREST doesn't expose arbitrary SQL aggregations, we
    fetch a lightweight projection and aggregate in Python.

    Returns a dict with keys: total, avg_score, label_counts, recent_7_days.
    """
    client = get_supabase_client()
    if client is None:
        return {"total": 0, "avg_score": 0, "label_counts": {}, "recent_7_days": 0}

    try:
        query = (
            client.table("predictions")
            .select("score, label, created_at")
        )
        if user_id is not None:
            query = query.eq("user_id", user_id)

        response = query.execute()
        rows = response.data or []

        if not rows:
            return {"total": 0, "avg_score": 0, "label_counts": {}, "recent_7_days": 0}

        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        scores = [r["score"] for r in rows if r.get("score") is not None]
        label_counts: Dict[str, int] = {}
        recent = 0

        for r in rows:
            if r.get("label"):
                label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1
            if r.get("created_at", "") >= cutoff:
                recent += 1

        return {
            "total": len(rows),
            "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
            "label_counts": label_counts,
            "recent_7_days": recent,
        }
    except Exception as exc:
        logger.error("[Supabase] sb_fetch_stats failed: %s", exc)
        return {"total": 0, "avg_score": 0, "label_counts": {}, "recent_7_days": 0}
