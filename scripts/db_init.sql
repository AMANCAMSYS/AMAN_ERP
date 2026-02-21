-- ─────────────────────────────────────────────────────────────────────────────
-- AMAN ERP — PostgreSQL initialisation script
-- Runs once on first `docker compose up` when the data volume is empty.
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable useful extensions (only in the default DB; tenant DBs get them on demand)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Ensure the aman superuser exists (docker env already creates it, but idempotent)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'aman') THEN
    CREATE ROLE aman WITH LOGIN SUPERUSER;
  END IF;
END
$$;
