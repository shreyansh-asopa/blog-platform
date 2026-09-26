from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_is_ok(settings: Settings):
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_database_is_up(settings: Settings):
    # Needs Postgres running: docker compose up -d db
    with TestClient(create_app(settings)) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_ready_returns_503_when_database_is_down(settings: Settings):
    # Port 1 has nothing listening, so the connection is refused
    down = settings.model_copy(update={"postgres_port": 1})
    with TestClient(create_app(down)) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["database"] == "down"
