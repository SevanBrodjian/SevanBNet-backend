-- One-time setup on the DEVELOPMENT Postgres (the sandbox):
--   psql "<development Postgres_db DATABASE_URL>" -f scripts/sandbox-marker.sql
-- scripts/sandbox-refresh only overwrites a database that has this table, and a local
-- checkout only connects to Postgres that has it. It lives outside the public schema,
-- so refreshes leave it in place. Production must never have it.

CREATE SCHEMA IF NOT EXISTS sandbox;
CREATE TABLE IF NOT EXISTS sandbox.marker (
  note text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO sandbox.marker (note)
SELECT 'The sandbox: a copy of production that scripts/sandbox-refresh may overwrite.'
WHERE NOT EXISTS (SELECT 1 FROM sandbox.marker);
