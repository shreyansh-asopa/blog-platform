# Database

PostgreSQL 16, run in Docker. Listens on `localhost:5432`.

Will contain:
- `init/` — scripts that run when the container is first created (e.g. creating the test database)
- `seed/` — sample users, posts and comments for local development
- `schema.md` — table reference and ER diagram

Schema changes are made with Alembic migrations in the backend, never by hand.
