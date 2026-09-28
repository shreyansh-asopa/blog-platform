# Troubleshooting

Problems you might hit while running or developing Lumen, and how to fix them. For the
basics (installing and starting), see the [user guide](USER_GUIDE.md#14-common-problems).

A good first step for any API problem:

```sh
docker compose ps                 # are blog-db and blog-api running and healthy?
docker compose logs --tail 50 api # the API's latest log lines
```

Every error response includes a `request_id`; search the API log for it to find the full
details, including any traceback.

## Contents

- [Starting up](#starting-up)
- [Website](#website)
- [Logging in](#logging-in)
- [Writing checks](#writing-checks)
- [Posts, covers and comments](#posts-covers-and-comments)
- [Development and tests](#development-and-tests)
- [Resetting](#resetting)

## Starting up

**`Cannot connect to the Docker daemon`**
Docker Desktop isn't running. Start it and wait until it says it is running.

**`Bind for 0.0.0.0:5432 failed: port is already allocated`** (or `8000`)
Another program, often a locally installed PostgreSQL, uses the port. Either stop it, or
set `POSTGRES_PORT=5433` / `API_PORT=8001` in `.env` and run `docker compose up -d` again.
If you move the API, start the website with `VITE_API_PROXY=http://localhost:8001 npm run dev`.

**`blog-api` keeps restarting, and the log mentions `jwt_secret`**
`JWT_SECRET` is missing or shorter than 32 characters. Generate one with
`openssl rand -hex 32`, put it in `.env`, then `docker compose up -d`.

**The API log shows `password authentication failed`**
`POSTGRES_PASSWORD` in `.env` changed after the database volume was created; the database
keeps the password it was created with. Put the old password back, or, if you don't need
the data, reset with `docker compose down -v` and start again.

**`curl localhost:8000/ready` returns an error or `database` isn't `up`**
The database is still starting. Wait a few seconds; `docker compose ps` should show
`blog-db` as `healthy`.

**Changes to backend code don't show up**
The Docker image holds a copy of the code. Rebuild it: `docker compose up -d --build api`.

## Website

**The page is blank or says it can't load posts**
The API isn't reachable. Check `curl localhost:8000/ready`, and that `npm run dev` is still
running in its terminal.

**`npm run dev` says port 5173 is in use**
Another dev server is running. Stop it, or run `npm run dev -- --port 5174`. The API only
allows browser calls from `CORS_ORIGINS` (default `http://localhost:5173`), but through
the dev server's proxy the browser never calls the API directly, so another port still
works.

**`npm install` fails or the build complains about the Node version**
Use Node.js 24: `node --version` should print `v24.x`.

**Covers don't show**
Cover images are served by the API at `/uploads`. Covers uploaded while the API ran
outside Docker are in `backend/uploads/`, not the Docker volume, and the reverse.

## Logging in

**Logged out unexpectedly**
Logins last 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`) and there is no refresh. Log in
again. Any 401 response logs the website out.

**"Too many login attempts, please wait a minute"**
5 attempts per minute per IP address and per username. Wait a minute. Counters reset when
the API restarts.

**No Admin link after making myself an admin**
Refresh the page. Check the change with the SQL shell:
`SELECT username, role FROM users;`. The username must match exactly as stored.

## Writing checks

Check what the API thinks is set up (from a logged-in browser tab, or with a token):

```sh
curl localhost:8000/api/v1/writing/status -H "Authorization: Bearer <token>"
# {"grammar":"ready","tone":"no_key","ai":null,"max_chars":20000}
```

**"The AI checks aren't set up yet" even though I added a key**
The API only reads `.env` when its container is created. Run
`docker compose up -d --build api`, then check the status again: `ai` should be `gemini` or
`groq`.

**"The AI service rejected the API key"**
The key is wrong, revoked, or for the other provider (`GEMINI_API_KEY` vs `GROQ_API_KEY`).
Create a new one and rebuild the API.

**"The AI service's free limit is used up for now" / "is busy right now"**
The free quota is spent or the provider is overloaded; Lumen already tried the fallback
model. Try later. Grammar results from LanguageTool still come back.

**"Too many checks, please wait a moment"**
All writing checks share 10 per minute per user (`WRITING_CHECKS_PER_MINUTE`).

**"Your post changed since this check."**
You edited the post after running the check. Run it again so the suggestions line up with
the text.

**A 413 error on a check**
The text is over 20,000 characters (`WRITING_MAX_CHARS`). Check a part of the post.

**Grammar results come with a note that a service was unavailable**
LanguageTool's public API or the AI didn't answer in time (30-second timeout). The other
one's results are shown; try again later for the rest.

## Posts, covers and comments

| Error | Meaning | Fix |
|---|---|---|
| 413 `file_too_large` | Cover over 5 MB | Use a smaller image |
| 415 `unsupported_file_type` | Not a real JPEG, PNG or WebP (checked from the file's bytes, not its name) | Convert the image |
| "Save a draft first, then add a cover." | A new post has no id yet | Click **Save draft** first |
| 422 `content_rejected` | Moderation refused the comment | Rephrase it |
| 404 on someone's draft | Drafts are private to their author and admins | Expected |
| Can't like a post | You can't like your own post, or it isn't published | Expected |

## Development and tests

**`uv: command not found`**
Install uv: https://docs.astral.sh/uv/getting-started/installation/

**Tests fail with `database "blog_test" does not exist`**
Your Postgres volume predates the init script that creates it. Create it once:

```sh
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" "$POSTGRES_TEST_DB"'
```

**Tests fail to connect to the database**
The `db` container must be running: `docker compose up -d db`.

**CI fails on `ruff format --check` or `npm run format:check`**
Run `uv run ruff format .` in `backend/` or `npm run format` in `frontend/` and commit the
result.

**CI fails on `alembic check`**
A model changed without a migration. Run
`uv run alembic revision --autogenerate -m "describe the change"`, read the generated file,
and commit it.

**`uv run uvicorn ...` says address already in use**
The API container is still on port 8000: `docker compose stop api`.

## Resetting

```sh
docker compose down -v          # removes the containers AND all data (accounts, posts, covers)
docker compose up -d --build    # fresh database; migrations run automatically
docker compose exec api python -m app.seed   # optional sample content
```

After a reset, log in again in the browser: old tokens belong to accounts that no longer
exist.
