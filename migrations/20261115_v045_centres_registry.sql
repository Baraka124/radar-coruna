-- RADAR-CORUÑA v0.45 | private centre registry
-- Additive migration. No synthetic/real centres are inserted automatically.
-- Apply to staging before deploying the v0.45 backend.
CREATE TABLE IF NOT EXISTS radar.centres (
    code text PRIMARY KEY CHECK (code ~ '^[A-Z][A-Z0-9_-]{2,23}$'),
    name text NOT NULL CHECK (char_length(btrim(name)) BETWEEN 3 AND 100),
    active boolean NOT NULL DEFAULT true,
    created_at text NOT NULL,
    updated_at text NOT NULL,
    created_by text NOT NULL
);
ALTER TABLE radar.centres ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON radar.centres FROM anon, authenticated;
CREATE INDEX IF NOT EXISTS idx_radar_centres_active_name ON radar.centres (active, name);

-- Existing historical accounts and invitations retain their original centre
-- strings. They are *not* silently mapped to invented centres.
-- The backend refuses to issue or accept invitations to unregistered/inactive centres.
-- The administrator must register the intended centre explicitly.
