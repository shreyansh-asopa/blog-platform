# Lumen

[![CI](https://github.com/shreyansh-asopa/blog-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/shreyansh-asopa/blog-platform/actions/workflows/ci.yml)

A multi-user blog platform where writers share ideas. Write posts in a rich-text editor,
check your writing before you publish, follow topics, and like and comment on other people's
posts. Admins moderate and every sensitive action is audited.

## Features

- **Reading**: a home feed, trending posts and topics, topic pages, author profiles and search.
- **Writing**: a rich-text editor (headings, lists, tables, links, colours, alignment), drafts,
  cover images, topics, publish and unpublish.
- **Check your writing**, right in the editor:
  - **Grammar**: spelling, grammar, punctuation and style, plus whole-sentence fixes by AI.
  - **Readability**: a score, reading time and long sentences, with "Simplify with AI".
  - **Tone**: how the post sounds, and rewrites to make it professional, friendly, confident
    or casual.
- **Community**: likes and comments, with automatic comment moderation.
- **Admin**: manage users' roles and browse the audit log.
- **Your data**: download all your posts as a CSV file.
- Light and dark themes, and layouts for phones.

## Tech stack

| Part | Built with |
|---|---|
| Frontend | React 19, TypeScript, Vite, TanStack Query, Tiptap editor |
| Backend | Python 3.13, FastAPI, SQLAlchemy (async), Alembic, managed with `uv` |
| Database | PostgreSQL 16 |
| Writing checks | LanguageTool (free, no key), Google Gemini or Groq (free API keys) |
| Runs with | Docker Compose; GitHub Actions for CI |

How it fits together (layers, data model, auth, key decisions): [docs/architecture.md](docs/architecture.md).

## Quick start

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/) and
[Node.js 24](https://nodejs.org/). Run these from the project folder:

**1. Create your settings file.** `.env` holds passwords and keys, so it is git-ignored and
never committed.

```sh
cp .env.example .env
```

Open `.env` and set:

- `POSTGRES_PASSWORD`: any password for the local database.
- `JWT_SECRET`: the key that signs login tokens. Generate one with `openssl rand -hex 32`.

**2. Start the database and the API.** The first run builds the API image, which takes a
minute or two. The database schema is set up automatically.

```sh
docker compose up -d --build
curl localhost:8000/ready        # {"status":"ok","database":"up"} once it's ready
```

**3. Add sample posts** (optional, but the site looks empty without them). Sample authors
get random passwords, which are printed once, so copy one if you want to log in as them.

```sh
docker compose exec api python -m app.seed
```

**4. Start the website.**

```sh
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**, register an account and start writing.

## Turning on the AI checks (optional)

Grammar works without any setup. Whole-sentence fixes, Tone and "Simplify with AI" need a
free AI key. Without one, the editor says the AI checks aren't set up, and everything else
works as usual.

**Google Gemini** (recommended):

1. Go to [Google AI Studio](https://aistudio.google.com/apikey), sign in and click
   **Create API key**.
2. Add it to `.env`: `GEMINI_API_KEY=your-key`.
3. Restart the API so it reads the key: `docker compose up -d --build api`.
4. Check it arrived: open the editor and click **Tone**. You should see the tone choices
   instead of "The tone check isn't set up yet", and the popups say your text is sent to
   Google Gemini.

**Groq** works the same way: create a key at [console.groq.com](https://console.groq.com/keys)
and set `GROQ_API_KEY`. If both keys are set, Gemini is used.

Keep the key private: don't paste it into chats, issues or commits.

## Everyday commands

Run from the project folder unless noted.

| What | Command |
|---|---|
| Start everything | `docker compose up -d` and `npm run dev` in `frontend/` |
| Rebuild after backend changes | `docker compose up -d --build api` |
| See the API logs | `docker compose logs -f api` |
| Stop (data is kept) | `docker compose stop` |
| Delete everything, including data | `docker compose down -v` |
| Interactive API docs | http://localhost:8000/docs |
| Make yourself an admin | see [Admins](backend/README.md#admins-and-the-audit-log) |

## Checks and tests

The same checks run on every pull request in CI.

```sh
# Backend (from backend/, with the database running)
uv sync                  # install dependencies, once
uv run pytest            # tests
uv run ruff check .      # lint
uv run ruff format .     # format

# Frontend (from frontend/)
npm run typecheck
npm run lint
npm run format:check     # npm run format fixes it
npm run build
```

## Troubleshooting

| Problem | What to do |
|---|---|
| Port 5432 or 8000 is already in use | Change `POSTGRES_PORT` or `API_PORT` in `.env`, then `docker compose up -d` |
| The website says "Could not reach the server" | The API isn't running: `docker compose ps`, then `docker compose logs api` |
| `/ready` says the database is down | Wait a few seconds after starting; if it stays down, check `docker compose logs db` |
| "The AI checks aren't set up yet" | Add `GEMINI_API_KEY` or `GROQ_API_KEY` to `.env` and rebuild the API |
| "The AI service's free limit is used up" | The free plan has a daily limit. It resets the next day, or use the other provider |
| "The AI service is busy right now" | The free model is overloaded; try again in a minute |
| An error shows a "Reference" code | Search the API logs for it: `docker compose logs api \| grep <code>` |

## Project layout

```
backend/     FastAPI app, migrations and tests         → backend/README.md
frontend/    React web app                             → frontend/README.md
database/    Postgres setup scripts                    → database/README.md
docs/        Architecture and design decisions
.github/     CI workflow
```

## License

[MIT](LICENSE)
