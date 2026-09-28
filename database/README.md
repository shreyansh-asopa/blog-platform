# Database

PostgreSQL 16, run in Docker. Listens on `localhost:5432`.

Contains:
- `init/01-create-test-db.sh`: runs when the data volume is first created and makes the
  separate test database (`POSTGRES_TEST_DB`, default `blog_test`) used by the backend tests.

Related, elsewhere in the repo:
- **Tables:** created and changed only by Alembic migrations in `backend/alembic/`, never by
  hand. The ER diagram is in [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md#7-data-model).
- **Sample content:** `docker compose exec api python -m app.seed` (from `backend/app/seed.py`).

## Usage

Run from the repo root:

```sh
cp .env.example .env                              # first time only, then set a password
docker compose up -d db                           # start Postgres in the background
docker compose ps                                 # status should show "healthy"
docker exec -it blog-db psql -U blog -d blog      # open a SQL shell (default user and db names)
docker compose logs -f db                         # follow the logs
docker compose stop db                            # stop (data is kept)
docker compose down -v                            # delete everything, including data
```

Scripts in `init/` run only when the data volume is first created. To run them again,
reset with `docker compose down -v`.
