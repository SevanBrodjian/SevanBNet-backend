# Control panel: technical decisions (2026-10-11)

Sources: PyPI, package source, official docs, a read-only query of the dev database.

## 1. Admin theme: django-unfold 0.108.0
Released 24 Sep 2026; Django 5.2–6.1, Python ≥3.12; fonts and JS bundled. `"unfold"` goes before `django.contrib.admin` and replaces `admin.site`; every ModelAdmin (User too) subclasses `unfold.admin.ModelAdmin`.
- Sidebar: `UNFOLD["SIDEBAR"] = {"show_all_applications": False, "navigation": [...]}`, seven `reverse_lazy("admin:…")` links.
- QR dashboard: `QRDashboard(UnfoldModelAdminViewMixin, TemplateView)` added in `QRRedirectAdmin.get_urls()`; template extends `admin/base.html`; inline JS/CSS move to static files; staff API moves under `/admin/qr/api/`.
- `UNFOLD["ENVIRONMENT"]` badge: Production / Sandbox / Local.
- Site settings: singleton ModelAdmin (no add/delete).
- allauth's `allauth/layouts/*.html` overridden to extend `unfold/layouts/unauthenticated.html`.

## 2. Passkeys: django-allauth[mfa] 65.19.7
django-otp-webauthn 0.10.3 has no trusted-device or backup-code UI (admin flow hand-built); django-passkeys 2.1 is passkey login only. allauth MFA has passkey second factor and passkey sign-in, recovery codes, built-in "Trust this browser" (signed cookie, voided when password or passkeys change), `secure_admin_login`; released 1 Oct 2026.
```python
INSTALLED_APPS += ["allauth", "allauth.account", "allauth.mfa"]  # + AccountMiddleware
LOGIN_URL, LOGIN_REDIRECT_URL = "/accounts/login/", "/admin/"
ACCOUNT_ADAPTER = "sevanbnet.auth.AccountAdapter"  # is_open_for_signup -> False
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_EMAIL_VERIFICATION = "none"
MFA_ADAPTER = "sevanbnet.auth.MFAAdapter"
MFA_SUPPORTED_TYPES = ["webauthn", "recovery_codes"]
MFA_PASSKEY_LOGIN_ENABLED = MFA_TRUST_ENABLED = MFA_RECOVERY_CODES_SHOW_ONCE = True
MFA_TRUST_COOKIE_AGE = timedelta(days=30)
ALLAUTH_TRUSTED_CLIENT_IP_HEADER = "X-Real-IP" if ON_RAILWAY else None


class MFAAdapter(DefaultMFAAdapter):  # default RP ID = request host
    def get_public_key_credential_rp_entity(self):
        host = context.request.get_host().partition(":")[0]
        return {"id": "sevanb.net" if host.endswith(".sevanb.net") else host, "name": "sevanb.net"}
```
One iCloud Keychain passkey then works on admin and dev-admin. On Railway: `admin.site.login = secure_admin_login(admin.site.login)`, staff without a passkey go to `mfa_add_webauthn`; localhost keeps password login.

## 3. Throttling: django-axes 8.3.1
DB-backed lockout shared across gunicorn workers; wired per axes' allauth guide (`AXES_USERNAME_FORM_FIELD = "login"`, LoginForm subclass, decorated LoginView). Backends: `AxesStandaloneBackend`, `ModelBackend`, allauth's; `AxesMiddleware` last.
```python
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = ["ip_address"]
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ADMIN = False
AXES_CLIENT_IP_CALLABLE = "sevanbnet.security.client_ip"
```
`client_ip`: `X-Real-IP` on Railway (set by its edge, per docs), `REMOTE_ADDR` locally; QR scans reuse it. allauth's own limits stay on.

## 4. Hosts, sessions, headers
- Middleware: admin hosts (admin., dev-admin., localhost, 127.0.0.1) redirect `/` to `/admin/`; elsewhere `/admin/` and `/accounts/` return 404. `/api/` and `/r/` everywhere.
- Both admin hosts in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`; CORS already has dev.sevanb.net and localhost:5173.
- `SESSION_COOKIE_AGE` 3 days; host-only cookies.
- CSP on admin hosts (report-only on dev first): `default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; media-src https://cdn.jsdelivr.net; frame-ancestors 'self'; base-uri 'none'; object-src 'none'`. Unfold's Alpine.js needs `'unsafe-eval'`; inline scripts stay blocked.

## 5. Media: GitHub Contents API + jsDelivr
`PUT /repos/{MEDIA_REPO}/contents/{path}` (`Authorization: Bearer`, `X-GitHub-Api-Version: 2026-03-10`), body `{"message", "content": <base64>, "branch": "main"}`; the 201 response has `commit.sha`. Unique paths, serial uploads. Token: fine-grained, SevanBNet-media only, Contents read/write. Repo must be public.
URL: `https://cdn.jsdelivr.net/gh/SevanBrodjian/SevanBNet-media@<commit.sha>/<path>`. Tested: `max-age=31536000, immutable`, correct svg/webp/mp4 types, byte ranges, CORS. jsDelivr caps GitHub files at 20 MB: reject larger. Unconfigured: the page explains and disables upload. The token is never logged.

## 6. Rebuild site: Railway GraphQL
```
POST https://backboard.railway.com/graphql/v2
Project-Access-Token: $RAILWAY_DEPLOY_TOKEN
{"query":"mutation($s:String!,$e:String!){serviceInstanceDeployV2(serviceId:$s,environmentId:$e)}",
 "variables":{"s":"$FRONTEND_SERVICE_ID","e":"$RAILWAY_ENVIRONMENT_ID"}}
```
Project tokens are scoped to one environment. Check `errors` even on HTTP 200. Set `NO_CACHE=1` on frontend services so cached build layers cannot skip the prerender. Without both variables the button is disabled with a note.

## 7. Databases
Dev: Postgres 15.5; timescaledb 2.12.2 + toolkit in `public`; no PostGIS; tables owned by `postgres`. Postgres_db has `DATABASE_URL` (proxy) and `DATABASE_PRIVATE_URL` (`railway.internal`); backend uses the proxy.
```sql
CREATE ROLE sandbox_reader LOGIN PASSWORD '<random>' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION CONNECTION LIMIT 2;
ALTER ROLE sandbox_reader SET default_transaction_read_only = on;
GRANT CONNECT ON DATABASE railway TO sandbox_reader;
GRANT USAGE ON SCHEMA public TO sandbox_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sandbox_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO sandbox_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON TABLES TO sandbox_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON SEQUENCES TO sandbox_reader;
```
Privileges are the guarantee; the read-only default is a second layer.

`scripts/sandbox-refresh` (bash; `brew install postgresql@15`):
1. Reads `SANDBOX_SOURCE_URL` (production backend variable) and development `Postgres_db.DATABASE_URL` via `railway variables --json`; never echoes.
2. Refuses if target equals the production proxy host:port, lacks a `sandbox.marker` table, or client ≠ v15.
3. `pg_dump -Fc --schema=public --no-owner --no-privileges --exclude-table-data=public.sevanbnet_scan --exclude-table-data=public.django_session --exclude-table-data='public.axes_*'` (`--schema` skips extensions, so TimescaleDB is untouched).
4. One `psql --single-transaction -v ON_ERROR_STOP=1`: drop non-extension relations in `public`, replay `pg_restore -f -` (TOC filtered to skip `SCHEMA public`). Failure keeps the old sandbox.
5. `migrate`; log counts (no URLs) to `logs/sandbox-refresh.log`.

Local: `scripts/sandbox-env` writes gitignored `.env.sandbox`; `.envrc` adds `dotenv_if_exists .env.sandbox`; delete it for SQLite. Settings refuse local Postgres without `sandbox.marker`.
Later: backend `DATABASE_URL=${{Postgres_db.DATABASE_PRIVATE_URL}}` (pre-deploy runs on the private network).

## 8. Markdown: Markdown 3.11 + nh3 0.3.7
`markdown.markdown(text, extensions=["extra", "nl2br", "sane_lists"])` keeps inline HTML and single-newline breaks; `nh3.Cleaner(url_schemes={"http", "https", "mailto"})` sanitizes. API serves `description_html`; frontend keeps DOMPurify.

## Risks
- jsDelivr forbids "general-purpose file or media hosting"; keep media modest, long videos on YouTube.
- RP ID override uses an adapter method: pin `~=65.19`.
- Restyling allauth pages is template work.
- Verify the project token and that `X-Real-IP` cannot be spoofed.
- Sandbox holds password hashes and passkeys: treat like production.
