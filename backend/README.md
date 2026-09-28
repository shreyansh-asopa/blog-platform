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

## Endpoints

| Method | Path | Auth | What it does |
|---|---|---|---|
| GET | `/health` | — | Process is up |
| GET | `/ready` | — | Database is reachable |
| POST | `/api/v1/auth/register` | — | Create an account (JSON: `email`, `username`, `password`) |
| POST | `/api/v1/auth/login` | — | Get a token (form: `username` = username or email, `password`) |
| GET | `/api/v1/users/me` | Bearer token | The logged-in user |
| GET | `/api/v1/users/{username}` | — | An author's public profile |
| GET | `/api/v1/posts?q=&author=&topic=&page=&size=` | — | Published posts, newest first (no `content`, max `size` 100); `q` searches, `author` and `topic` filter |
| GET | `/api/v1/posts/trending?limit=` | — | Published posts with the most likes plus comments in the last 7 days |
| GET | `/api/v1/posts/{slug}` | Optional | One post; drafts only for their author or an admin |
| POST | `/api/v1/posts` | Bearer token | Create a draft (JSON: `title`, `content`, optional `excerpt`) |
| PATCH | `/api/v1/posts/{id}` | Author or admin | Change any of `title`, `content`, `excerpt` |
| POST | `/api/v1/posts/{id}/publish` | Author or admin | Make a draft public |
| POST | `/api/v1/posts/{id}/unpublish` | Author or admin | Turn it back into a draft |
| DELETE | `/api/v1/posts/{id}` | Author or admin | Soft delete (hidden everywhere, kept in the database) |
| POST | `/api/v1/posts/{id}/cover` | Author or admin | Set or replace the cover (multipart field `file`: JPEG, PNG or WebP, max 5 MB) |
| DELETE | `/api/v1/posts/{id}/cover` | Author or admin | Remove the cover |
| GET | `/uploads/covers/{name}` | — | The cover image itself (the URL is in the post's `cover_image`) |
| GET | `/api/v1/topics` | — | All topics |
| GET | `/api/v1/topics/trending?limit=` | — | Topics whose posts got the most likes and comments in the last 7 days |
| GET | `/api/v1/topics/{slug}` | — | One topic |
| PUT | `/api/v1/posts/{id}/like` | Bearer token | Like a published post (not your own); repeating is harmless |
| DELETE | `/api/v1/posts/{id}/like` | Bearer token | Remove your like |
| GET | `/api/v1/posts/{id}/comments?page=&size=` | Optional | A post's comments, oldest first |
| POST | `/api/v1/posts/{id}/comments` | Bearer token | Comment on a published post (JSON: `content`) |
| DELETE | `/api/v1/comments/{id}` | Comment author, post author or admin | Soft delete a comment |
| GET | `/api/v1/me/posts?status=` | Bearer token | Your own posts, drafts included; filter with `draft`/`published` |
| GET | `/api/v1/me/posts/export?format=csv&status=` | Bearer token | Download all your posts as a CSV file |
| GET | `/api/v1/admin/users?search=&role=&page=&size=` | Admin | All users |
| PATCH | `/api/v1/admin/users/{id}/role` | Admin | Make a user `admin` or `user` (JSON: `role`); not your own |
| GET | `/api/v1/admin/audit-logs?action=&actor_id=&page=&size=` | Admin | Who did what, newest first |
| GET | `/api/v1/writing/status` | Bearer token | Which writing checks are set up (`ai` is `gemini`, `groq` or `null`) |
| POST | `/api/v1/writing/grammar` | Bearer token | Word mistakes and AI sentence fixes (JSON: `text`) |
| POST | `/api/v1/writing/tone` | Bearer token | How the text sounds, with rewrites (JSON: `text`, `target`) |
| POST | `/api/v1/writing/simplify` | Bearer token | A shorter version of one sentence (JSON: `sentence`) |

Post rules: the slug follows a draft's title but is frozen once published, so shared links
keep working. The excerpt is generated from the content unless you set your own.
Someone else's draft returns 404, so drafts can't be discovered.
Every post includes `like_count` and `comment_count`; `GET /posts/{slug}` also says `liked_by_me`.

Comments are checked by moderation before they are saved (422 `content_rejected` if refused).
By default a built-in word list decides. Set `MODERATION_API_URL` in `.env` to use an external
API instead; if it is down, comments are accepted unchecked and a warning is logged.

Writing checks: grammar asks LanguageTool (free, no key) and, when an AI key is set, Google
Gemini or Groq at the same time; if one of them is down, the other's results still come
back with a note. The AI calls use the providers' OpenAI-style APIs
(`app/integrations/llm.py`), and a fallback model is tried when the first is busy, out of
quota or retired. Nothing sent to the checks is stored. They share a limit of 10 checks per
minute per user, and a post can be at most 20,000 characters.

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

Covers: the file type is checked from the file's own bytes, not its name, and each file is
saved under a random name. Too large is 413 `file_too_large`; not an image is 415
`unsupported_file_type`. Replacing or removing a cover deletes the old file. Files live in
`UPLOAD_DIR` (default `uploads/`, a Docker volume in Compose) behind a `Storage` interface
(`app/integrations/storage.py`), so they can move to S3 later.

Export: the CSV is streamed in batches, so even a large export never sits in memory all at
once. Cells that a spreadsheet would run as a formula (starting with `=`, `+`, `-`, `@`) are
prefixed with `'`, and the file starts with a UTF-8 byte-order mark so Excel reads accents.

## Every request

- **Request id**: each response has an `X-Request-ID` header (send your own to keep it),
  also found in every error body and log line, so one request can be traced end to end.
- **Errors** always look like `{"error": {"code", "message", "request_id"}}`. Validation
  errors (422 `validation_error`) add `details: [{"field", "message"}]`. Crashes are a
  500 `internal_error` without any internal details; the traceback goes to the log.
- **Logs** are JSON lines (`LOG_FORMAT=console` for a terminal), one per request with
  method, path, status and duration. Successful health checks are not logged.
- **CORS**: only the origins in `CORS_ORIGINS` may call the API from a browser.
- **GZip** for responses over 1 KB.
- **Rate limits** (429 `rate_limited` with `Retry-After`): 5 login attempts per minute per
  IP address and username, 10 comments and 10 writing checks per minute per user. Counts are kept in memory,
  so they are per process and reset on restart.

## Admins and the audit log

The role is read from the database on every request, so promoting
or demoting someone takes effect at once, even with a token they already have. Role changes,
every post or comment deletion, and admins editing or (un)publishing someone else's post are
recorded in `audit_logs`, in the same transaction as the change itself. Entries survive the
deletion of the user who acted (`actor` becomes `null`). The first admin has to be made by hand:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
# then, at the psql prompt:
UPDATE users SET role = 'admin' WHERE username = 'you';
```
