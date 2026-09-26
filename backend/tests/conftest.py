from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.core.config import Settings

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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
