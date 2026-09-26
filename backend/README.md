# Backend

FastAPI REST API (Python 3.13, managed with `uv`). Runs on `http://localhost:8000`, docs at `/docs`.

Contains:
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

## Endpoints so far

| Method | Path | Auth | What it does |
|---|---|---|---|
| GET | `/health` | — | Process is up |
| GET | `/ready` | — | Database is reachable |
| POST | `/api/v1/auth/register` | — | Create an account (JSON: `email`, `username`, `password`) |
| POST | `/api/v1/auth/login` | — | Get a token (form: `username` = username or email, `password`) |
| GET | `/api/v1/users/me` | Bearer token | The logged-in user |
| GET | `/api/v1/posts?page=&size=` | — | Published posts, newest first (no `content`, max `size` 100) |
| GET | `/api/v1/posts/{slug}` | Optional | One post; drafts only for their author or an admin |
| POST | `/api/v1/posts` | Bearer token | Create a draft (JSON: `title`, `content`, optional `excerpt`) |
| PATCH | `/api/v1/posts/{id}` | Author or admin | Change any of `title`, `content`, `excerpt` |
| POST | `/api/v1/posts/{id}/publish` | Author or admin | Make a draft public |
| POST | `/api/v1/posts/{id}/unpublish` | Author or admin | Turn it back into a draft |
| DELETE | `/api/v1/posts/{id}` | Author or admin | Soft delete (hidden everywhere, kept in the database) |
| GET | `/api/v1/me/posts?status=` | Bearer token | Your own posts, drafts included; filter with `draft`/`published` |

Post rules: the slug follows a draft's title but is frozen once published, so shared links
keep working. The excerpt is generated from the content unless you set your own.
Someone else's draft returns 404, so drafts can't be discovered.

Try it in the browser at `/docs`: register, then click **Authorize**, log in, and call `/users/me`.

```sh
curl -X POST localhost:8000/api/v1/auth/login -d 'username=ada&password=...'
curl localhost:8000/api/v1/users/me -H "Authorization: Bearer <access_token>"
```

Errors share one shape: `{"error": {"code": "conflict", "message": "Email is already registered"}}`.

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
