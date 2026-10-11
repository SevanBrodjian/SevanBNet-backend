# sevanb.net backend

Django app behind [sevanb.net](https://www.sevanb.net). It serves:

- a read-only JSON API (`/api/projects/`, `/api/papers/`, `/api/posts/`, `/api/site/`) consumed by the React frontend; see [docs/api.md](docs/api.md)
- the control panel (Django admin with Unfold) at admin.sevanb.net and dev-admin.sevanb.net, with passkey sign-in, the QR code manager, media uploads and a Rebuild site button; see [docs/control-panel.md](docs/control-panel.md)
- QR short links at `go.sevanb.net/r/<code>/`

Every response is sent with `X-Robots-Tag: noindex` so that only the frontend appears in search results.

## Local development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 8000   # always http://localhost:8000
```

Locally the app uses `db.sqlite3`, `DEBUG=True` and a throwaway secret key, so no configuration is needed. The panel is at http://localhost:8000/admin/ (password sign-in). To work on a copy of production instead, use the sandbox: [docs/sandbox.md](docs/sandbox.md).

Checks (the same ones CI runs):

```sh
uv run ruff check && uv run ruff format --check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

## Deployment

Railway deploys `dev` to the development environment and `main` to production, each only after CI passes. Changes go from `dev` to `main` through a pull request.

The service's build, migrate, start and health-check settings are defined in `.railway/railway.ts` (Railway infrastructure as code). Railway does not read that file on deploy, so after editing it apply it explicitly:

```sh
cd .railway && npm install && cd ..
railway environment development
railway config plan     # dry run: check it says "0 to destroy" and touches only backend_django
railway config apply
```

Repeat with `railway environment production`. The file declares the partial `backend`, so it can only ever change the `backend_django` service; the database and frontend services are outside its scope.

Each Railway environment needs these variables:

| Variable | Notes |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required. Long random string, different per environment. |
| `DATABASE_URL` | Required. Reference the environment's Postgres service (ideally its `DATABASE_PRIVATE_URL`). |
| `QR_BASE_URL` | Production: `https://go.sevanb.net` |
| `SITE_URL` | Development: `https://dev.sevanb.net`. Production leaves it unset (`https://www.sevanb.net`). |
| `DJANGO_DEBUG` | Leave unset. Debug is off on Railway unless this is `True`. |
| `MEDIA_REPO`, `GITHUB_MEDIA_TOKEN` | Optional. Media uploads; off without them. |
| `RAILWAY_DEPLOY_TOKEN`, `FRONTEND_SERVICE_ID` | Optional. The Rebuild site button; off without them. |
| `SANDBOX_SOURCE_URL` | Production only, read by `scripts/sandbox-refresh`, not by the app. |

Details for the optional ones are in [docs/control-panel.md](docs/control-panel.md#setup-reference).

`RAILWAY_ENVIRONMENT_NAME` is set by Railway automatically. Its presence is what switches the app into deployment mode, where missing required variables stop the deploy instead of falling back to local defaults.
