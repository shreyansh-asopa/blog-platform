import logging
import re

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import RateLimiter

POSTS = "/api/v1/posts"
LOGIN = "/api/v1/auth/login"
FRONTEND = "http://localhost:5173"


# --- Request ids ---


def test_every_response_has_a_request_id(client: TestClient):
    first = client.get("/health").headers["X-Request-ID"]
    second = client.get("/health").headers["X-Request-ID"]

    assert re.fullmatch(r"[0-9a-f]{32}", first)
    assert first != second


def test_a_callers_request_id_is_kept_if_it_is_safe(client: TestClient):
    kept = client.get("/health", headers={"X-Request-ID": "trace-abc.123"})
    replaced = client.get("/health", headers={"X-Request-ID": "x" * 65})

    assert kept.headers["X-Request-ID"] == "trace-abc.123"
    assert replaced.headers["X-Request-ID"] != "x" * 65


def test_request_is_logged_with_its_id(client: TestClient, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        response = client.get("/api/v1/nowhere")

    [line] = [r.msg for r in caplog.records if r.name == "app.access"]
    assert line["path"] == "/api/v1/nowhere"
    assert line["status"] == 404
    assert line["request_id"] == response.headers["X-Request-ID"]
    assert line["duration_ms"] >= 0


# --- One error shape for everything ---


def test_unknown_url_uses_the_error_shape(client: TestClient):
    response = client.get("/api/v1/nowhere")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_wrong_method_uses_the_error_shape(client: TestClient):
    response = client.put("/health")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_validation_errors_say_which_field_is_wrong(client: TestClient, make_user):
    ada = make_user("ada")

    response = client.post(POSTS, json={"title": "x" * 201}, headers=ada.headers)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    fields = {d["field"] for d in error["details"]}
    assert fields == {"body.title", "body.content"}


def test_crashes_become_a_clean_500(client: TestClient, caplog):
    @client.app.get("/boom")
    async def boom():
        raise RuntimeError("secret internal detail")

    with caplog.at_level(logging.ERROR):
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    # The client learns nothing about the code; the log gets the full story
    assert "secret" not in response.text
    assert "secret internal detail" in caplog.text
    assert response.headers["X-Request-ID"] == response.json()["error"]["request_id"]


# --- CORS and compression ---


def test_the_frontend_may_call_the_api(client: TestClient):
    response = client.options(
        POSTS,
        headers={"Origin": FRONTEND, "Access-Control-Request-Method": "POST"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND


def test_other_websites_may_not(client: TestClient):
    response = client.get(POSTS, headers={"Origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers


def test_large_responses_are_compressed(client: TestClient):
    big = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
    small = client.get("/health", headers={"Accept-Encoding": "gzip"})

    assert big.headers["content-encoding"] == "gzip"
    assert "content-encoding" not in small.headers


# --- Rate limits ---


def login(client: TestClient, username: str):
    return client.post(LOGIN, data={"username": username, "password": "wrong-password"})


def test_login_attempts_are_limited(client: TestClient, make_user):
    make_user("ada")
    make_user("grace")  # each make_user logs in once, which counts too

    for _ in range(4):
        assert login(client, "ada").status_code == 401
    blocked = login(client, "ADA")

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert 1 <= int(blocked.headers["Retry-After"]) <= 60
    # Other accounts are not affected
    assert login(client, "grace").status_code == 401


def test_commenting_is_limited(client: TestClient, make_user):
    ada = make_user("ada")
    post = client.post(POSTS, json={"title": "T", "content": "C"}, headers=ada.headers).json()
    client.post(f"{POSTS}/{post['id']}/publish", headers=ada.headers)
    url = f"{POSTS}/{post['id']}/comments"

    statuses = [
        client.post(url, json={"content": f"Hi {i}"}, headers=ada.headers).status_code
        for i in range(11)
    ]

    assert statuses == [201] * 10 + [429]


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_rate_limiter_window_slides():
    clock = FakeClock()
    limiter = RateLimiter(clock)

    assert limiter.hit("k", limit=2, window=60) is None
    clock.now += 30
    assert limiter.hit("k", limit=2, window=60) is None
    assert limiter.hit("k", limit=2, window=60) == pytest.approx(30)
    # The first hit drops out of the window 60 seconds after it happened
    clock.now += 30
    assert limiter.hit("k", limit=2, window=60) is None
    assert limiter.hit("other", limit=2, window=60) is None


def test_rate_limiter_forgets_old_keys():
    clock = FakeClock()
    limiter = RateLimiter(clock)
    for i in range(10):
        limiter.hit(f"visitor-{i}", limit=5, window=60)

    clock.now += 61
    for _ in range(RateLimiter._SWEEP_EVERY):
        limiter.hit("regular", limit=10**6, window=60)

    assert set(limiter._hits) == {"regular"}


def test_successful_health_checks_are_not_logged(client: TestClient, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/health")

    assert not [r for r in caplog.records if r.name == "app.access"]
