# sevanb.net backend: working rules

## Fixed local addresses (do not change)
- Backend: http://localhost:8000 (`uv run python manage.py runserver 8000`)
- Admin: http://localhost:8000/admin/
- Frontend: http://localhost:5173 (see the frontend repo)

## Databases: never risk production data
- Production content is real and backed up; it is edited only through the production admin.
- Never point a local command at the production `DATABASE_URL`.
- Every migration is tested first on a copy of the data, then on the development environment, and reaches production only after Sevan has taken a Railway backup and said go.
- Schema changes that rename, merge or drop columns copy the data into the new fields before removing the old ones.

## Branches and deploys
- Railway deploys `dev` to the development environment and `main` to production, each only after CI passes. Never push `main` without Sevan's explicit go-ahead.
- Railway service settings live in `.railway/railway.ts`. Change them only with `railway config plan` first (it must say "0 to destroy"), then apply that pinned plan. Never pass `--confirm-destructive`. When a release needs new settings, merge the code first and apply the settings right after.

## Before committing
- `uv run ruff check`, `uv run ruff format --check`, `uv run python manage.py makemigrations --check --dry-run` and `uv run python manage.py test`, judged by exit code.
- Commit with an explicit pathspec (`git commit -m "..." -- <paths>`).
