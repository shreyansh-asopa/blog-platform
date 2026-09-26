import uuid
from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import create_access_token

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/users/me"

ADA = {"email": "ada@example.com", "username": "ada", "password": "correct-horse-battery"}


def register(client: TestClient, **overrides) -> dict:
    response = client.post(REGISTER, json=ADA | overrides)
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, identifier: str = "ada", password: str = ADA["password"]):
    # OAuth2 login is a form post, not JSON
    return client.post(LOGIN, data={"username": identifier, "password": password})


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Register ---


def test_register_returns_the_new_user_without_the_password(client: TestClient):
    user = register(client)

    assert user["email"] == "ada@example.com"
    assert user["username"] == "ada"
    assert user["role"] == "user"
    assert user["is_active"] is True
    uuid.UUID(user["id"])
    assert "password" not in user
    assert "hashed_password" not in user


def test_register_lowercases_the_email(client: TestClient):
    user = register(client, email="Ada@Example.COM")

    assert user["email"] == "ada@example.com"


@pytest.mark.parametrize(
    ("second", "message"),
    [
        ({"username": "ada2"}, "Email is already registered"),
        ({"email": "ADA@example.com", "username": "ada2"}, "Email is already registered"),
        ({"email": "other@example.com"}, "Username is already taken"),
        ({"email": "other@example.com", "username": "ADA"}, "Username is already taken"),
    ],
)
def test_register_rejects_duplicates(client: TestClient, second: dict, message: str):
    register(client)

    response = client.post(REGISTER, json=ADA | second)

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": message,
            "request_id": response.headers["X-Request-ID"],
        }
    }


def test_register_keeps_the_username_as_typed(client: TestClient):
    # Only comparisons ignore case; the name shows the way its owner wrote it
    assert register(client, username="Ada_Lovelace")["username"] == "Ada_Lovelace"


@pytest.mark.parametrize(
    "bad",
    [
        {"email": "not-an-email"},
        {"username": "ab"},
        {"username": "has spaces"},
        {"password": "short"},
    ],
)
def test_register_validates_input(client: TestClient, bad: dict):
    response = client.post(REGISTER, json=ADA | bad)

    assert response.status_code == 422


# --- Login ---


@pytest.mark.parametrize("identifier", ["ada", "ADA", "ada@example.com", "ADA@example.com"])
def test_login_with_username_or_email(client: TestClient, identifier: str):
    register(client)

    response = login(client, identifier)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.parametrize(
    ("identifier", "password"),
    [("ada", "wrong-password"), ("nobody", ADA["password"])],
)
def test_login_failures_share_one_message(client: TestClient, identifier: str, password: str):
    register(client)

    response = login(client, identifier, password)

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Incorrect email/username or password"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_token_carries_only_the_expected_claims(client: TestClient, settings: Settings):
    register(client)
    token = login(client).json()["access_token"]

    claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert set(claims) == {"sub", "role", "iat", "exp"}
    assert claims["role"] == "user"


# --- Current user ---


def test_me_returns_the_logged_in_user(client: TestClient):
    user = register(client)
    token = login(client).json()["access_token"]

    response = client.get(ME, headers=auth_header(token))

    assert response.status_code == 200
    assert response.json() == user


def test_me_without_a_token(client: TestClient):
    response = client.get(ME)

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Not authenticated"


def test_me_with_an_expired_token(client: TestClient, settings: Settings):
    user = register(client)
    token = create_access_token(
        uuid.UUID(user["id"]), "user", settings, expires_delta=timedelta(minutes=-1)
    )

    response = client.get(ME, headers=auth_header(token))

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Token has expired"


def test_me_with_a_token_signed_by_someone_else(client: TestClient, settings: Settings):
    user = register(client)
    forged_settings = settings.model_copy(update={"jwt_secret": "x" * 64})
    token = create_access_token(uuid.UUID(user["id"]), "admin", forged_settings)

    response = client.get(ME, headers=auth_header(token))

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid token"


def test_me_with_a_garbage_token(client: TestClient):
    response = client.get(ME, headers=auth_header("not.a.jwt"))

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid token"
