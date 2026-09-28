# Development guide

How to work on Lumen's code: run it with live reload, change the database, run the checks
CI runs, and follow the project's conventions. To just run and use Lumen, see the
[user guide](USER_GUIDE.md).

## Contents

- [Tools](#tools)
- [Running with live reload](#running-with-live-reload)
- [Project layout](#project-layout)
- [Database migrations](#database-migrations)
- [Checks and tests](#checks-and-tests)
- [Conventions](#conventions)
- [Adding a feature, end to end](#adding-a-feature-end-to-end)
- [Git workflow](#git-workflow)
- [Deploying](#deploying)

## Tools

| Tool | Used for |
|---|---|
| Docker Desktop | PostgreSQL (and the API, when not running it locally) |
| Node.js 24 + npm | The frontend |
| [uv](https://docs.astral.sh/uv/) | Python 3.13, the backend's virtualenv and dependencies (only for running the backend outside Docker) |

## Running with live reload

**Frontend** (always run locally; reloads on save):

```sh
cd frontend
npm install
npm run dev            # http://localhost:5173
```

The dev server proxies `/api` and `/uploads` to `http://localhost:8000`. To point it at
another API, set `VITE_API_PROXY`, for example `VITE_API_PROXY=http://localhost:8001 npm run dev`.

**Backend**, either way:

- In Docker (simplest): `docker compose up -d --build api` after each backend change.
- On your machine with auto-reload:

  ```sh
  docker compose up -d db          # database only
  docker compose stop api          # free port 8000
  cd backend
  uv sync
  uv run uvicorn app.main:app --reload
  ```

  Covers uploaded while running this way go to `backend/uploads/`, not the Docker volume.

Logs are JSON lines by default; set `LOG_FORMAT=console` in `.env` for a terminal-friendly
format.

## Project layout

The top-level structure is in the [README](../README.md#project-structure). Where to look
for common changes:

| To change | Look in |
|---|---|
| An endpoint | `backend/app/api/v1/routes/` (HTTP) → `backend/app/services/` (rules) → `backend/app/repositories/` (SQL) |
| Request/response fields | `backend/app/schemas/` and `frontend/src/api/types.ts` |
| A table | `backend/app/models/`, then a migration |
| Settings | `backend/app/core/config.py` and `.env.example` |
| Who may do what | `backend/app/permissions.py` |
| Outside services | `backend/app/integrations/` |
| A page | `frontend/src/pages/` (component + `.module.css`) and the route in `frontend/src/App.tsx` |
| API calls from the UI | `frontend/src/api/endpoints.ts` |
| The editor or writing checks | `frontend/src/components/RichEditor.tsx`, `frontend/src/components/writing/`, `frontend/src/lib/` |
| Colours and themes | `frontend/src/styles/global.css`, `frontend/src/theme/` |

## Database migrations

Tables change only through Alembic. The API container runs `alembic upgrade head` on start.
From `backend/`:

```sh
uv run alembic revision --autogenerate -m "add bookmarks"   # after changing a model
uv run alembic upgrade head                                 # apply it
uv run alembic downgrade -1                                 # undo the latest
uv run alembic check                                        # models and migrations agree?
```

Read every generated migration before applying it: autogenerate misses some things, such as
dropping Postgres enum types in `downgrade()`, or data changes like seeding topics. CI fails
if a model changes without a matching migration.

## Checks and tests

These are exactly what [CI](../.github/workflows/ci.yml) runs on every pull request and every
push to `main`:

```sh
# backend/ (the db container must be running)
uv sync --frozen
uv run ruff check .
uv run ruff format --check .      # `uv run ruff format .` fixes it
uv run alembic upgrade head && uv run alembic check
uv run pytest -q                  # 263 tests

# frontend/
npm ci
npm run typecheck
npm run lint
npm run format:check              # `npm run format` fixes it
npm run build
```

CI also builds the API's Docker image.

**About the tests:**

- They run against a separate database, `POSTGRES_TEST_DB` (default `blog_test`), created
  by `database/init/01-create-test-db.sh` when the Postgres volume is first made. If your
  volume is older than that script, create it once:
  `docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" "$POSTGRES_TEST_DB"'`.
- Outside services are replaced with fakes or `httpx2.MockTransport`, so the suite works
  offline and never spends AI quota.
- Run one file or test with `uv run pytest tests/test_posts.py -k slug`.

## Conventions

**Backend**

- Keep to the layers in [ARCHITECTURE.md](ARCHITECTURE.md#4-backend-layers): routes stay
  thin, services hold the rules, repositories hold the SQL.
- Raise the domain exceptions in `app/core/exceptions.py`; never build error responses by
  hand, so every error keeps the `{"error": {...}}` shape.
- Every setting has a default in `Settings` and is documented in `.env.example`.
- An outside service gets a `Protocol`, a real implementation, and a factory in
  `app/integrations/`, created once in `main.py`'s lifespan, so tests can fake it.
- Anything an admin does to someone else's content writes an audit entry in the same
  transaction.

**Frontend**

- Only `src/api/` calls `fetch`. Server data goes through TanStack Query.
- Each page and component has its own CSS module; colours come from the CSS variables in
  `global.css`, so both themes keep working.
- Check new UI in light and dark themes and at phone width.

**Both:** comments explain *why*, not *what*; user-facing text says "Lumen".

## Adding a feature, end to end

1. Model and migration (if the data changes).
2. Schema, repository, service, route; register a new router in `app/api/v1/router.py`.
3. Tests in `backend/tests/`, including the permission and error cases.
4. Types and endpoint in `frontend/src/api/`, then the UI.
5. Update [API.md](API.md) and, if user-visible, the [user guide](USER_GUIDE.md) and the
   README features table.

## Git workflow

- `main` is always releasable. Work on a branch (`feat/...`, `fix/...`, `docs/...`).
- Commit messages are short imperatives, e.g. "Add trending topics and trending posts".
- Open a pull request into `main`; merge only when CI is green.
- Never commit `.env` or real keys. `.env.example` holds placeholders only.

## Deploying

Lumen has **no hosted deployment or release pipeline yet**; it runs locally with Docker
Compose. What exists, and what a real deployment would still need:

**Ready now**

- The API is a Docker image (`backend/Dockerfile`) that applies migrations and then starts
  Uvicorn on port 8000. `/health` and `/ready` suit load-balancer and container health
  checks.
- `npm run build` produces a static site in `frontend/dist/` that any static host or web
  server can serve.
- All configuration comes from environment variables.

**Still needed**

1. **A reverse proxy** (e.g. Nginx, Caddy or a platform's router) with HTTPS, serving
   `frontend/dist/` and forwarding `/api` and `/uploads` to the API, as the Vite dev server
   does locally. The SPA also needs every unknown path to fall back to `index.html`.
2. **Secrets** from the platform's secret store: a new `JWT_SECRET`, a strong
   `POSTGRES_PASSWORD`, and any AI or moderation keys.
3. **`CORS_ORIGINS`** set to the real site address (not needed if the site and API share
   one origin behind the proxy).
4. **A managed PostgreSQL 16** with backups, reached through `POSTGRES_HOST` and friends.
5. **Persistent storage for covers:** a volume mounted at the upload folder, or an S3
   implementation of the `Storage` interface in `app/integrations/storage.py`.

**Known limits**

- Rate-limit counters live in memory, so run **one API instance** (or add a shared store
  such as Redis before scaling out).
- Tokens last 30 minutes with no refresh; users log in again.
- Uploads are served by the API itself via `/uploads`.
