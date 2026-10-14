# Databases: production and the sandbox

- **Production** (the production environment's `Postgres_db`) is the only real data. It is edited only at https://admin.sevanb.net.
- **The sandbox** is the development environment's `Postgres_db`. The dev site (dev.sevanb.net once that domain is added, and dev-admin.sevanb.net) and, when you want, your local backend both use it. It is a copy of production that can be thrown away and refreshed at any time, so editing or migrating it never risks anything.

A refresh makes the sandbox an exact copy of production (including the record of applied migrations), then runs the migrations of the code you have checked out, so every new migration is rehearsed on real data before production sees it.

The sandbox holds password hashes and passkey public keys: treat it like production (don't share its URL or dumps). It never holds QR scan rows (visitor IPs), sessions, login-attempt records or backup codes; the refresh leaves those out.

## Refresh the sandbox

```sh
scripts/sandbox-refresh
```

Needs `railway login` and the Postgres 15 tools (`brew install postgresql@15`). Run it from the branch whose migrations you want to rehearse (usually `dev`). It takes a few seconds and logs what it did, without any URLs or passwords, to `logs/sandbox-refresh.log`:

1. Reads two URLs from Railway without printing them: `SANDBOX_SOURCE_URL` (a production backend variable that connects as the read-only `sandbox_reader` role) and the development `Postgres_db` `DATABASE_URL`. Both connections require TLS.
2. Refuses to continue unless the source session is read-only and the role can't write, the target has the `sandbox.marker` table and the source doesn't, the two are different servers, and everything is Postgres 15.
3. Dumps production's `public` schema, leaving out the data of `sevanbnet_scan`, `django_session` and `axes_*`. Extensions (TimescaleDB) aren't touched.
4. In one transaction on the sandbox: drops everything in `public` except extension objects, restores the dump, deletes backup codes. If any step fails, the old sandbox stays as it was.
5. Runs `manage.py migrate` against the sandbox and logs row counts before and after.

Because production is read only through `sandbox_reader`, which can only `SELECT`, the refresh cannot change production even if the script had a bug.

The dev backend keeps running during a refresh; requests in that second may fail.

## Use the sandbox from your laptop

```sh
scripts/sandbox-env        # writes .env.sandbox (gitignored, readable only by you)
```

Add `dotenv_if_exists .env.sandbox` to `.envrc` once and run `direnv allow`. From then on `uv run python manage.py runserver 8000` uses the sandbox, and the control panel shows a "Local · sandbox data" badge. To go back to the local `db.sqlite3`, delete `.env.sandbox`.

Locally the backend refuses to use any Postgres database without the `sandbox.marker` table, so a production URL pasted by mistake stops before anything happens. Tests always use a throwaway SQLite database.

Local admin sign-in is password only (passkeys are for admin.sevanb.net and dev-admin.sevanb.net).

## One-time setup

1. **Marker on the sandbox.** Against the development `Postgres_db`:
   ```sh
   psql "<development Postgres_db DATABASE_URL>" -f scripts/sandbox-marker.sql
   ```
2. **Read-only role on production.** Take a Railway backup of production first. Then, against the production `Postgres_db`:
   ```sh
   SANDBOX_PW=$(openssl rand -hex 24)
   psql "<production Postgres_db DATABASE_URL>" -v password="$SANDBOX_PW" -f scripts/sandbox-reader.sql
   ```
   The SQL is in `scripts/sandbox-reader.sql`: a login role with `SELECT` on the `public` tables and sequences (including future ones), read-only sessions by default, at most 2 connections, nothing else.
3. **Store the source URL** on the production backend service as `SANDBOX_SOURCE_URL` (the backend itself never reads it; the script does):
   ```
   postgresql://sandbox_reader:<SANDBOX_PW>@<production RAILWAY_TCP_PROXY_DOMAIN>:<RAILWAY_TCP_PROXY_PORT>/railway?sslmode=require
   ```
   Railway can build it from references: `postgresql://sandbox_reader:<SANDBOX_PW>@${{Postgres_db.RAILWAY_TCP_PROXY_DOMAIN}}:${{Postgres_db.RAILWAY_TCP_PROXY_PORT}}/${{Postgres_db.PGDATABASE}}?sslmode=require`.

   **Treat this URL like the production database URL.** The role can't change anything, but it can read everything, including live admin sessions (a session is a signed-in panel, past the passkey) and QR scan IPs. Postgres can't exclude those tables from it, because `pg_dump` must lock every table it dumps.
4. Run `scripts/sandbox-refresh` once and check the log.

## Private network for the backend

The backend reaches Postgres through Railway's public TCP proxy today, which is the likely cause of the occasional ~2 s first request on the dev site (a new connection through the proxy). Switching the backend service's variable in both environments to

```
DATABASE_URL=${{Postgres_db.DATABASE_PRIVATE_URL}}
```

keeps the traffic on the private network (`*.railway.internal`). The pre-deploy `migrate` runs inside Railway too, so it works there as well. Local tools (`scripts/sandbox-env`, `scripts/sandbox-refresh`) keep using the public URL of `Postgres_db`, which this doesn't change.
