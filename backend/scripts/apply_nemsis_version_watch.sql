-- Create nemsis_version_watch table (single row) for NEMSIS update notifications.
-- Run this if you prefer to apply the NEMSIS watch table without resolving multiple Alembic heads.
-- Usage: psql $DATABASE_URL -f backend/scripts/apply_nemsis_version_watch.sql

CREATE TABLE IF NOT EXISTS nemsis_version_watch (
    id INTEGER NOT NULL PRIMARY KEY,
    last_known_version VARCHAR(32) NOT NULL DEFAULT '3.5.1',
    last_checked_at TIMESTAMP WITH TIME ZONE,
    last_notified_version VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

INSERT INTO nemsis_version_watch (id, last_known_version)
VALUES (1, '3.5.1')
ON CONFLICT (id) DO NOTHING;

-- Optional: record that this revision was applied (so Alembic doesn't try to run it later)
-- INSERT INTO alembic_version (version_num) VALUES ('20260130_nemsis') ON CONFLICT DO NOTHING;
