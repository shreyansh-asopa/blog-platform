# Backend

FastAPI REST API (Python 3.13, managed with `uv`). Runs on `http://localhost:8000`, docs at `/docs`.

Contains:
- `app/`: core, models, schemas, repositories, services, integrations, API routes
- `alembic/`: database migrations
- `tests/`: pytest suite
- `pyproject.toml` and `uv.lock`: dependencies (installed with `uv sync`)

Every endpoint, with auth, errors and limits, is documented in [docs/API.md](../docs/API.md).
How the layers fit together is in [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

## Running

Everything in Docker (from the repo root):

```sh
docker compose up -d --build     # build the API image and start db + api
curl localhost:8000/health       # {"status":"ok"}
curl localhost:8000/ready        # {"status":"ok","database":"up"}
open http://localhost:8000/docs  # interactive API docs
```

On your machine, with auto-reload while editing (from `backend/`, with the db container running):

```sh
docker compose stop api          # free port 8000 first
uv sync                          # install dependencies into .venv
uv run uvicorn app.main:app --reload
```

Try it in the browser at `/docs`: register, then click **Authorize**, log in, and call `/users/me`.

```sh
curl -X POST localhost:8000/api/v1/auth/login -d 'username=ada&password=...'
curl localhost:8000/api/v1/users/me -H "Authorization: Bearer <access_token>"
```

## Database migrations

Schema changes go through Alembic, never by hand. The Docker container runs
`alembic upgrade head` automatically on start. On your machine (from `backend/`):

```sh
uv run alembic upgrade head                                # apply all pending migrations
uv run alembic current                                     # which migration the database is on
uv run alembic history                                     # list all migrations
uv run alembic revision --autogenerate -m "add posts"      # new migration after changing a model
uv run alembic downgrade -1                                # undo the latest migration
```

Always read a generated migration before running it. Autogenerate can miss things,
such as dropping Postgres enum types in `downgrade()`.

## Checks

```sh
uv run pytest                    # tests (needs the db container running)
uv run ruff check .              # lint
uv run ruff format .             # auto-format
```

Tests use a separate database (`POSTGRES_TEST_DB`) and replace every outside service
(moderation, LanguageTool, the AI) with a fake, so they never touch the internet.

## Sample content

```sh
docker compose exec api python -m app.seed
```

Adds 10 authors and 35 published posts with topics, covers (from `app/seed_covers/`), likes
and comments. Running it again adds nothing twice; it only fills in topics or covers that
are missing. The authors get random passwords, printed once, so the public repo holds no
working login. The cover art is drawn by `scripts/draw_sample_art.py`.

## Admins

The role is read from the database on every request, so promoting or demoting someone
takes effect at once, even with a token they already have. The first admin has to be made
by hand:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
# then, at the psql prompt:
UPDATE users SET role = 'admin' WHERE username = 'you';
```
