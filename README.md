# sevanb.net backend

Django app behind [sevanb.net](https://www.sevanb.net). It serves:

- a read-only JSON API (`/api/projects/`, `/api/publications/`, `/api/blogposts/`) consumed by the React frontend
- the Django admin for managing that content
- the QR code manager: public short links at `go.sevanb.net/r/<code>/` and a staff-only dashboard at `/qr/`

Every response is sent with `X-Robots-Tag: noindex` so that only the frontend appears in search results.

## Local development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Locally the app uses `db.sqlite3`, `DEBUG=True` and a throwaway secret key, so no configuration is needed.

Checks (the same ones CI runs):

```sh
uv run ruff check && uv run ruff format --check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

## Deployment

Railway deploys `dev` to the development environment and `main` to production. The build, migrate, start and health-check steps are in `railway.json`. Changes go from `dev` to `main` through a pull request.

Each Railway environment needs these variables:

| Variable | Notes |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required. Long random string, different per environment. |
| `DATABASE_URL` | Required. Reference the environment's Postgres service. |
| `QR_BASE_URL` | Production: `https://go.sevanb.net` |
| `SITE_URL` | Optional. Defaults to `https://www.sevanb.net`. |
| `DJANGO_DEBUG` | Leave unset. Debug is off on Railway unless this is `True`. |

`RAILWAY_ENVIRONMENT_NAME` is set by Railway automatically. Its presence is what switches the app into deployment mode, where missing required variables stop the deploy instead of falling back to local defaults.
