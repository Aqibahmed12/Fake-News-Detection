-- =============================================================================
-- Migration: Create predictions table
-- Run this once in the Supabase SQL Editor:
--   https://supabase.com/dashboard/project/ztiqgcjicxtgqsrvqwwl/editor
-- =============================================================================

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

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS predictions_user_id_idx
    ON predictions (user_id);

CREATE INDEX IF NOT EXISTS predictions_api_key_id_idx
    ON predictions (api_key_id);

CREATE INDEX IF NOT EXISTS predictions_created_at_idx
    ON predictions (created_at DESC);

-- Optional: Row Level Security
-- Enable RLS so the anon key can only read its own rows.
-- Comment this block out if you want unrestricted access.
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (idempotent via DO block)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename  = 'predictions'
          AND policyname = 'Allow service role full access'
    ) THEN
        EXECUTE '
            CREATE POLICY "Allow service role full access"
                ON predictions
                FOR ALL
                USING (true)
                WITH CHECK (true)
        ';
    END IF;
END
$$;
