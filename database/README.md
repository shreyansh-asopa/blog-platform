# Database

PostgreSQL 16, run in Docker. Listens on `localhost:5432`.

Will contain:
- `init/` — scripts that run when the container is first created (e.g. creating the test database)
- `seed/` — sample users, posts and comments for local development
- `schema.md` — table reference and ER diagram

Schema changes are made with Alembic migrations in the backend, never by hand.

## Usage

Run from the repo root:

```sh
cp .env.example .env                              # first time only, then set a password
docker compose up -d db                           # start Postgres in the background
docker compose ps                                 # status should show "healthy"
docker exec -it blog-db psql -U blog -d blog      # open a SQL shell
docker compose logs -f db                         # follow the logs
docker compose stop db                            # stop (data is kept)
docker compose down -v                            # delete everything, including data
```

Scripts in `init/` run only when the data volume is first created. To run them again,
reset with `docker compose down -v`.
