import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import create_engine
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def settings() -> Settings:
    """App settings pointed at the test database, never the development one."""
    base = Settings()
    return base.model_copy(update={"postgres_db": base.postgres_test_db})


@pytest.fixture(scope="session", autouse=True)
def migrated_database(settings: Settings) -> None:
    """Rebuild the test database from the migrations once per test run.

    Downgrading first wipes leftovers from the previous run and also proves every
    migration can be undone.
    """
    config = Config(BACKEND_DIR / "alembic.ini")
    config.attributes["database_url"] = settings.database_url
    command.downgrade(config, "base")
    command.upgrade(config, "head")


async def _empty_tables(settings: Settings) -> None:
    engine = create_engine(settings)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE users CASCADE"))
    await engine.dispose()


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """An API client on the test database, starting from empty tables."""
    asyncio.run(_empty_tables(settings))
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
