import asyncio
from collections.abc import Callable, Iterator
from dataclasses import dataclass
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
def client(settings: Settings, tmp_path: Path) -> Iterator[TestClient]:
    """An API client on the test database, starting from empty tables.

    Uploads go to a fresh temporary folder, so tests never touch the real one.
    """
    asyncio.run(_empty_tables(settings))
    app_settings = settings.model_copy(update={"upload_dir": tmp_path / "uploads"})
    with TestClient(create_app(app_settings)) as test_client:
        yield test_client


@dataclass
class LoggedInUser:
    id: str
    username: str
    headers: dict[str, str]


async def _set_role(settings: Settings, username: str, role: str) -> None:
    engine = create_engine(settings)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET role = :role WHERE username = :username"),
            {"role": role, "username": username},
        )
    await engine.dispose()


@pytest.fixture
def make_user(client: TestClient, settings: Settings) -> Callable[..., LoggedInUser]:
    """Register and log in a user; returns their id and ready-to-use auth headers."""

    def _make_user(username: str, *, admin: bool = False) -> LoggedInUser:
        password = "correct-horse-battery"
        response = client.post(
            "/api/v1/auth/register",
            json={"email": f"{username}@example.com", "username": username, "password": password},
        )
        assert response.status_code == 201, response.text
        if admin:
            asyncio.run(_set_role(settings, username, "admin"))
        token = client.post(
            "/api/v1/auth/login", data={"username": username, "password": password}
        ).json()["access_token"]
        return LoggedInUser(response.json()["id"], username, {"Authorization": f"Bearer {token}"})

    return _make_user


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
