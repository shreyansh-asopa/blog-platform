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
| PUT | `/api/v1/posts/{id}/like` | Bearer token | Like a published post (not your own); repeating is harmless |
| DELETE | `/api/v1/posts/{id}/like` | Bearer token | Remove your like |
| GET | `/api/v1/posts/{id}/comments?page=&size=` | Optional | A post's comments, oldest first |
| POST | `/api/v1/posts/{id}/comments` | Bearer token | Comment on a published post (JSON: `content`) |
| DELETE | `/api/v1/comments/{id}` | Comment author, post author or admin | Soft delete a comment |
| GET | `/api/v1/me/posts?status=` | Bearer token | Your own posts, drafts included; filter with `draft`/`published` |
| PATCH | `/api/v1/admin/users/{id}/role` | Admin | Make a user `admin` or `user` (JSON: `role`); not your own |
| GET | `/api/v1/admin/audit-logs?action=&actor_id=&page=&size=` | Admin | Who did what, newest first |

Post rules: the slug follows a draft's title but is frozen once published, so shared links
keep working. The excerpt is generated from the content unless you set your own.
Someone else's draft returns 404, so drafts can't be discovered.
Every post includes `like_count` and `comment_count`; `GET /posts/{slug}` also says `liked_by_me`.

Comments are checked by moderation before they are saved (422 `content_rejected` if refused).
By default a built-in word list decides. Set `MODERATION_API_URL` in `.env` to use an external
API instead; if it is down, comments are accepted unchecked and a warning is logged.

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

Admins and the audit log: the role is read from the database on every request, so promoting
or demoting someone takes effect at once, even with a token they already have. Role changes,
every post or comment deletion, and admins editing or (un)publishing someone else's post are
recorded in `audit_logs`, in the same transaction as the change itself. Entries survive the
deletion of the user who acted (`actor` becomes `null`). The first admin has to be made by hand:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
# then, at the psql prompt:
UPDATE users SET role = 'admin' WHERE username = 'you';
```
