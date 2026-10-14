-- One-time setup on the PRODUCTION Postgres, run only with Sevan's go-ahead:
--   psql "<production DATABASE_URL>" -v password='<long random password>' -f scripts/sandbox-reader.sql
-- Creates sandbox_reader, the role scripts/sandbox-refresh copies production through.
-- It can read every table and nothing else; its sessions are also read-only by default.

CREATE ROLE sandbox_reader LOGIN PASSWORD :'password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION CONNECTION LIMIT 2;
ALTER ROLE sandbox_reader SET default_transaction_read_only = on;

GRANT CONNECT ON DATABASE :"DBNAME" TO sandbox_reader;
GRANT USAGE ON SCHEMA public TO sandbox_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sandbox_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO sandbox_reader;
-- Tables that future migrations create are readable too.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON TABLES TO sandbox_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON SEQUENCES TO sandbox_reader;
