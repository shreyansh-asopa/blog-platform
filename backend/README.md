# Backend

FastAPI REST API (Python 3.13, managed with `uv`). Runs on `http://localhost:8000`, docs at `/docs`.

Will contain:
- `app/` — core, models, schemas, repositories, services, API routes
- `tests/` — pytest suite
- `pyproject.toml` — dependencies (installed with `uv sync`)

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
